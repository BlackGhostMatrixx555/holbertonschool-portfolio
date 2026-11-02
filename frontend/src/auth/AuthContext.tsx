/**
 * Contexte d'authentification : partage l'utilisateur connecté avec toute l'application.
 *
 * Choix de stockage du jeton : sessionStorage.
 * - Le jeton disparaît à la fermeture de l'onglet (moins d'exposition qu'avec localStorage).
 * - Il reste lisible par du JavaScript : la protection contre le XSS repose donc sur
 *   React, qui échappe tout le texte affiché (aucun dangerouslySetInnerHTML ici).
 * Une évolution possible serait un cookie HttpOnly posé par l'API.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setAuthToken, setUnauthorizedHandler } from '../api/client'
import { fetchMe, login as loginRequest } from '../api/endpoints'
import type { User } from '../api/types'

const TOKEN_KEY = 'camporga.token'

export interface AuthState {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthState | null>(null)

function readStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(() => {
    const stored = readStoredToken()
    setAuthToken(stored) // le client HTTP doit connaître le jeton dès le premier rendu
    return stored
  })

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
  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: fetchMe,
    enabled: token !== null,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await loginRequest(email, password)
      setAuthToken(access_token)
      const user = await fetchMe()
      try {
        sessionStorage.setItem(TOKEN_KEY, access_token)
      } catch {
        /* navigation privée stricte : la session ne survivra pas au rechargement */
      }
      queryClient.setQueryData(['me', access_token], user)
      setToken(access_token)
      return user
    },
    [queryClient],
  )

  const value = useMemo<AuthState>(
    () => ({
      user: token ? (meQuery.data ?? null) : null,
      isLoading: token !== null && meQuery.isPending,
      login,
      logout,
    }),
    [token, meQuery.data, meQuery.isPending, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
