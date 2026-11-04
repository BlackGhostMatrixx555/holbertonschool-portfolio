/**
 * Outils de test : rendu avec les mêmes fournisseurs que l'application, et faux serveur.
 * (Ce fichier n'est utilisé que par les tests, jamais en production.)
 */

// Client de requêtes TanStack Query et son fournisseur, comme dans main.tsx.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// render : monte un composant React dans un DOM de test (jsdom). Fourni par Testing Library.
import { render } from '@testing-library/react'

// Type ReactElement : type TypeScript désignant un élément JSX (ex. <Page />). "type" indique un import uniquement typé, effacé à la compilation.
import type { ReactElement } from 'react'

// MemoryRouter : routeur qui garde l'historique en mémoire au lieu de l'URL du navigateur (adapté aux tests).
// Route et Routes : déclarent les routes de test.
import { MemoryRouter, Route, Routes } from 'react-router-dom'

// vi : utilitaire de Vitest pour créer des fonctions simulées (mocks) et modifier des globaux.
import { vi } from 'vitest'

// Fournisseur d'authentification de l'application, pour que les composants testés aient accès au contexte utilisateur.
import { AuthProvider } from '../auth/AuthContext'

/**
 * Rend un composant avec les fournisseurs de l'application.
 * @param ui       l'élément React à tester
 * @param route    l'URL initiale simulée (par défaut "/")
 * @param path     le motif de route sous lequel le composant est monté (par défaut "*", qui capture tout)
 */
export function renderWithProviders(ui: ReactElement, { route = '/', path = '*' }: { route?: string; path?: string } = {}) {
  // Client de test : retry désactivé, pour que les erreurs apparaissent immédiatement dans les tests et ne soient pas retentées.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })

  return render(
    // Même ordre de fournisseurs que dans main.tsx : requêtes, routeur, authentification.
    <QueryClientProvider client={queryClient}>
      {/* initialEntries : définit l'URL de départ de ce test. */}
      <MemoryRouter initialEntries={[route]}>
        <AuthProvider>
          <Routes>
            {/* Route qui affiche le composant testé. */}
            <Route path={path} element={ui} />

            {/* Routes "sentinelles" : elles permettent de vérifier qu'une redirection a bien eu lieu (le texte affiché indique la page atteinte). */}
            <Route path="/connexion" element={<p>Page de connexion</p>} />
            <Route path="/espace" element={<p>Espace organisateur</p>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/**
 * Type d'une fonction de réponse simulée : elle reçoit les options de la requête et l'URL,
 * et renvoie un statut HTTP et un corps optionnels.
 */
type Handler = (init: RequestInit | undefined, url: string) => { status?: number; body?: unknown }

/**
 * Remplace fetch par un faux serveur : chaque clé "MÉTHODE /chemin" renvoie une réponse.
 * Retourne le mock pour vérifier les appels effectués.
 *
 * Exemple : mockApi({ 'GET /camps': { body: [] }, 'POST /auth/login': { status: 401 } })
 */
export function mockApi(routes: Record<string, Handler | { status?: number; body?: unknown }>) {
  // vi.fn : crée une fonction espion qui enregistre ses appels, et l'implémente avec la fonction async fournie.
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    // Normalise l'URL en chaîne de caractères.
    const url = String(input)

    // Retire le domaine et le préfixe /api, puis la query string (?...) : on ne garde que le chemin.
    const path = url.replace(/^https?:\/\/[^/]+\/api/, '').split('?')[0]

    // Clé de recherche, ex. "GET /camps". Méthode par défaut : GET, comme fetch.
    const key = `${init?.method ?? 'GET'} ${path}`

    const route = routes[key]

    // Si la route n'est pas simulée, renvoie une erreur 500 explicite pour faciliter le débogage du test.
    if (!route) return new Response(JSON.stringify({ detail: `Route non simulée : ${key}` }), { status: 500 })

    // Si la route est une fonction, on l'appelle pour obtenir la réponse (utile pour réagir au contenu de la requête).
    // Sinon, on utilise l'objet tel quel. Les valeurs par défaut donnent un statut 200.
    const { status = 200, body } = typeof route === 'function' ? route(init, url) : route

    // Construit une vraie Response du navigateur. Le corps est null si body est undefined (ex. réponse 204).
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  // Remplace la variable globale fetch par le mock, pour que tout le code de l'application l'utilise.
  // Il faut restaurer l'original après les tests (vi.unstubAllGlobals()).
  vi.stubGlobal('fetch', fetchMock)

  // Retourne le mock pour pouvoir vérifier ensuite les appels, ex. expect(fetchMock).toHaveBeenCalledWith(...).
  return fetchMock
}