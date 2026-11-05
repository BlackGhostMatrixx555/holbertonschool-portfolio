/**
 * Point d'entrée : installe les "fournisseurs" globaux autour de l'application.
 * - QueryClientProvider : cache des données de l'API (TanStack Query)
 * - BrowserRouter : navigation entre les pages sans recharger
 * - AuthProvider : utilisateur connecté
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ApiError } from './api/client'
import App from './App'
import { AuthProvider } from './auth/AuthContext'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // une donnée est considérée fraîche 30 s
      // Pas de nouvelle tentative sur une erreur 4xx (inutile : la requête est refusée).
      retry: (failureCount, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 2,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
