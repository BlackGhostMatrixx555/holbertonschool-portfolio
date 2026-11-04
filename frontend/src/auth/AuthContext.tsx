/**
 * Contexte d'authentification : partage l'utilisateur connecté avec toute l'application.
 *
 * Choix de stockage du jeton : sessionStorage.
 * - Le jeton disparaît à la fermeture de l'onglet (moins d'exposition qu'avec localStorage).
 * - Il reste lisible par du JavaScript : la protection contre le XSS repose donc sur
 *   React, qui échappe tout le texte affiché (aucun dangerouslySetInnerHTML ici).
 * Une évolution possible serait un cookie HttpOnly posé par l'API.
 */
// useQuery : récupère et met en cache une donnée asynchrone. useQueryClient : accès au cache global.
import { useQuery, useQueryClient } from '@tanstack/react-query'
// createContext : crée un canal de partage de données. useCallback / useMemo : mémorisent fonctions et valeurs.
// useEffect / useState : effets de bord et état local. ReactNode : type d'un contenu React.
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
// Fonctions du client HTTP : définir le jeton envoyé et enregistrer le gestionnaire d'erreur 401.
import { setAuthToken, setUnauthorizedHandler } from '../api/client'
// Appels à l'API pour le profil et les connexions. login est renommé pour éviter le conflit avec la fonction du contexte.
import { fetchMe, loginTwoFactor, login as loginRequest } from '../api/endpoints'
import type { User } from '../api/types'

// Clé sous laquelle le jeton est enregistré dans sessionStorage.
const TOKEN_KEY = 'camporga.token'

/** Résultat de l'étape 1 : soit connecté, soit un code 2FA est demandé. */
// Type union : soit l'utilisateur est connecté, soit il doit encore saisir son code 2FA.
export type LoginResult = { status: 'logged-in'; user: User } | { status: 'two-factor'; tempToken: string }

// Forme de la valeur partagée avec toute l'application.
export interface AuthState {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<LoginResult>
  completeTwoFactor: (tempToken: string, code: string) => Promise<User>
  refreshUser: () => Promise<void>
  logout: () => void
}

// eslint-disable-next-line react-refresh/only-export-components
// Désactive la règle ESLint qui signale qu'un fichier exporte à la fois un composant et autre chose.
// null par défaut : useAuth vérifie cette valeur pour détecter l'absence de AuthProvider.
export const AuthContext = createContext<AuthState | null>(null)

// Lit le jeton stocké. La lecture peut échouer (navigation privée stricte, stockage bloqué), d'où le try.
function readStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

// Fournisseur : entoure l'application et fournit l'état d'authentification à tous les composants enfants.
export function AuthProvider({ children }: { children: ReactNode }) {
  // Client de requêtes, utilisé pour vider ou mettre à jour le cache.
  const queryClient = useQueryClient()
  // Le jeton est lu une seule fois au premier rendu via une fonction d'initialisation.
  const [token, setToken] = useState<string | null>(() => {
    const stored = readStoredToken()
    setAuthToken(stored) // le client HTTP doit connaître le jeton dès le premier rendu
    return stored
  })

  // Déconnexion : efface le jeton partout puis vide le cache pour ne pas exposer les données de l'utilisateur précédent.
  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(TOKEN_KEY)
    } catch {
      /* stockage indisponible : rien à effacer */
    }
    setAuthToken(null)
    setToken(null)
    queryClient.clear() // on oublie toutes les données de l'utilisateur précédent
  }, [queryClient])

  // Jeton expiré ou compte désactivé : l'API répond 401, on déconnecte.
  // Le gestionnaire est enregistré à l'arrivée et retiré au démontage pour éviter les doublons.
  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  // Requête du profil. Elle ne part que si un jeton existe (enabled), sans nouvelle tentative (retry: false).
  // La clé inclut le jeton : un nouveau jeton force une nouvelle requête.
  // staleTime : le profil est considéré à jour pendant 5 minutes sans nouvelle requête.
  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: fetchMe,
    enabled: token !== null,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  /** Ouvre la session avec un jeton de session (après 1 ou 2 étapes). */
  const startSession = useCallback(
    async (accessToken: string) => {
      setAuthToken(accessToken)
      // Récupère le profil avant d'enregistrer le jeton : si cela échoue, la session n'est pas ouverte.
      const user = await fetchMe()
      try {
        sessionStorage.setItem(TOKEN_KEY, accessToken)
      } catch {
        /* navigation privée stricte : la session ne survivra pas au rechargement */
      }
      // Injecte directement le profil dans le cache : évite une seconde requête identique.
      queryClient.setQueryData(['me', accessToken], user)
      setToken(accessToken)
      return user
    },
    [queryClient],
  )

  // Étape 1 de connexion : e-mail et mot de passe.
  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const response = await loginRequest(email, password)
      // 2FA activée : l'API ne donne qu'un jeton temporaire, il faut le code à 6 chiffres.
      if (response.requires_2fa && response.temp_token) {
        return { status: 'two-factor', tempToken: response.temp_token }
      }
      // Pas de 2FA : la session s'ouvre directement. Le ?? '' évite un undefined, mais un jeton vide sera rejeté par l'API.
      return { status: 'logged-in', user: await startSession(response.access_token ?? '') }
    },
    [startSession],
  )

  // Étape 2 de connexion : échange du jeton temporaire et du code 2FA contre un jeton de session.
  const completeTwoFactor = useCallback(
    async (tempToken: string, code: string) => {
      const response = await loginTwoFactor(tempToken, code)
      return startSession(response.access_token ?? '')
    },
    [startSession],
  )

  /** Recharge le profil après une modification (téléphone, 2FA...). */
  // Marque les données « me » comme périmées : React Query les recharge automatiquement.
  const refreshUser = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['me'] })
  }, [queryClient])

  // Valeur fournie au contexte. Mémorisée pour que les consommateurs ne se réaffichent que si une dépendance change.
  // user n'est renseigné que si un jeton existe ; isLoading est vrai pendant le premier chargement du profil.
  const value = useMemo<AuthState>(
    () => ({
      user: token ? (meQuery.data ?? null) : null,
      isLoading: token !== null && meQuery.isPending,
      login,
      completeTwoFactor,
      refreshUser,
      logout,
    }),
    [token, meQuery.data, meQuery.isPending, login, completeTwoFactor, refreshUser, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}