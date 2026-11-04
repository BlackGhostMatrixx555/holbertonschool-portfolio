/**
 * Point d'entrée : installe les "fournisseurs" globaux autour de l'application.
 * (Bloc de commentaire JSDoc : décrit le rôle du fichier, lisible par les outils et l'IDE.)
 */

// Hook/client de TanStack Query : gère le cache, les requêtes et les états (chargement, erreur, succès) pour les données de l'API.
// QueryClientProvider rend ce cache accessible à tous les composants enfants.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// StrictMode : outil de développement qui signale les usages dangereux (effets de bord, API obsolètes) et double certains appels en dev.
import { StrictMode } from 'react'

// createRoot : API React 18+ qui crée la racine de rendu dans le DOM.
import { createRoot } from 'react-dom/client'

// BrowserRouter : active la navigation côté client via l'API History (URLs propres, sans rechargement de page).
import { BrowserRouter } from 'react-router-dom'

// Classe d'erreur personnalisée levée par le client HTTP, qui porte le code de statut (ex. 404, 500).
import { ApiError } from './api/client'

// Composant racine de l'application (définit les routes et l'interface).
import App from './App'

// Fournisseur de contexte d'authentification : expose l'utilisateur connecté à toute l'app.
import { AuthProvider } from './auth/AuthContext'

// Feuille de styles globale (Tailwind et styles de base).
import './index.css'

// Création du client de requêtes avec les options par défaut appliquées à toutes les requêtes.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Durée pendant laquelle une donnée reste "fraîche" : pendant 30 s, pas de nouvelle requête réseau automatique.
      // 30_000 : séparateur numérique (ES2021) pour lisibilité, vaut 30000 millisecondes.
      staleTime: 30_000, // une donnée est considérée fraîche 30 s

      // Fonction de décision de nouvelle tentative appelée à chaque échec.
      // failureCount : nombre d'échecs déjà survenus ; error : l'erreur levée.
      // Retourne true pour réessayer, false pour abandonner.
      // Pas de nouvelle tentative sur une erreur 4xx (inutile : la requête est refusée).
      // Maximum 2 tentatives supplémentaires (failureCount < 2) pour les autres erreurs (réseau, 5xx).
      retry: (failureCount, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 2,

      // Désactive le rechargement automatique des données quand l'utilisateur revient sur l'onglet.
      refetchOnWindowFocus: false,
    },
  },
})

// Sélectionne l'élément <div id="root"> du HTML et y monte l'application React.
// "!" (non-null assertion) : indique à TypeScript que l'élément existe toujours ; à défaut, getElementById renverrait null.
createRoot(document.getElementById('root')!).render(
  // StrictMode englobe toute l'application (détection d'erreurs en développement uniquement).
  <StrictMode>
    {/* Rend le cache de requêtes disponible à tous les composants. */}
    <QueryClientProvider client={queryClient}>
      {/* Active le routage : chaque URL correspond à une vue. Doit englober les composants qui utilisent les routes. */}
      <BrowserRouter>
        {/* Fournit l'utilisateur connecté. Placé à l'intérieur du routeur, donc accessible aux pages et à la navigation. */}
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)