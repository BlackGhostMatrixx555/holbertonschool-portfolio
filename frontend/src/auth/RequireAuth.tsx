/**
 * Garde de route : n'affiche la page que si l'utilisateur est connecté
 * (et super admin si `adminOnly`). Sinon, redirige vers la connexion.
 *
 * Ce contrôle améliore l'expérience mais ne protège rien à lui seul :
 * la vraie vérification des droits est faite par l'API sur chaque requête.
 */
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Spinner } from '../components/ui'
import { isSuperAdmin, useAuth } from './useAuth'

export function RequireAuth({ children, adminOnly = false }: { children: ReactNode; adminOnly?: boolean }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <Spinner label="Vérification de la session…" />
  if (!user) return <Navigate to="/connexion" replace state={{ from: location.pathname }} />
  if (adminOnly && !isSuperAdmin(user.role)) return <Navigate to="/espace" replace />
  return <>{children}</>
}
