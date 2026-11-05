/** Accès au contexte d'authentification, séparé du fichier du composant pour le rechargement rapide (Vite). */
import { useContext } from 'react'
import { AuthContext, type AuthState } from './AuthContext'

/** Donne accès à la session (utilisateur connecté, login, logout) depuis n'importe quel composant. */
export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  // Erreur explicite si un composant est utilisé hors de <AuthProvider> (bug de développement).
  if (!context) throw new Error('useAuth doit être utilisé dans <AuthProvider>.')
  return context
}

/** Vrai si le rôle donne accès à l'administration (utilisateurs, sauvegardes). */
export const isSuperAdmin = (role: string | undefined) => role === 'super_admin'
