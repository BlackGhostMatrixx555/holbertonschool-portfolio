/**
 * Garde de route : n'affiche la page que si l'utilisateur est connecté
 * (et super admin si `adminOnly`). Sinon, redirige vers la connexion.
 *
 * Ce contrôle améliore l'expérience mais ne protège rien à lui seul :
 * la vraie vérification des droits est faite par l'API sur chaque requête.
 */
// ReactNode : type d'un contenu React (élément, texte, fragment...).
import type { ReactNode } from 'react'
// Navigate : composant qui redirige. useLocation : donne l'URL courante.
import { Navigate, useLocation } from 'react-router-dom'
import { Spinner } from '../components/ui'
import { isSuperAdmin, useAuth } from './useAuth'

// children : la page protégée. adminOnly : si vrai, seul le super admin peut voir la page.
export function RequireAuth({ children, adminOnly = false }: { children: ReactNode; adminOnly?: boolean }) {
  // Lit l'utilisateur courant et l'état de chargement de la session.
  const { user, isLoading } = useAuth()
  // Mémorise la page demandée pour y revenir après la connexion.
  const location = useLocation()

  // Tant que la session est en cours de vérification, on affiche un indicateur plutôt que de rediriger à tort.
  if (isLoading) return <Spinner label="Vérification de la session…" />
  // Pas d'utilisateur connecté : redirection vers la connexion.
  // replace évite d'ajouter la page à l'historique ; state.from transmet l'URL d'origine.
  if (!user) return <Navigate to="/connexion" replace state={{ from: location.pathname }} />
  // Page réservée aux admins mais utilisateur sans ce rôle : retour à l'espace organisateur.
  if (adminOnly && !isSuperAdmin(user.role)) return <Navigate to="/espace" replace />
  // Tous les contrôles sont passés : on affiche la page. Le fragment évite un élément wrapper inutile.
  return <>{children}</>
}