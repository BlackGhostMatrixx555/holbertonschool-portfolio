// useContext : lit la valeur fournie par un Context React, ici l'état d'authentification.
import { useContext } from 'react'
// AuthContext : le contexte créé dans AuthContext.tsx. AuthState : le type de la valeur qu'il contient.
import { AuthContext, type AuthState } from './AuthContext'

// Hook personnalisé : donne accès à l'utilisateur connecté et aux fonctions d'authentification.
// Son nom commence par "use" : c'est la convention qui permet à React de vérifier les règles des hooks.
export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  // Garde-fou : si le composant n'est pas enveloppé par <AuthProvider>, le contexte vaut sa valeur par défaut
  // (généralement null) et l'erreur signale l'oubli plutôt que de provoquer un bug plus loin.
  if (!context) throw new Error('useAuth doit être utilisé dans <AuthProvider>.')
  return context
}

// Vérifie si le rôle donné correspond au super administrateur.
// Le paramètre accepte undefined, car l'utilisateur peut ne pas être encore chargé ou être déconnecté.
export const isSuperAdmin = (role: string | undefined) => role === 'super_admin'