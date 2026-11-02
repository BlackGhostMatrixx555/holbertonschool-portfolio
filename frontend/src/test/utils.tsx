/** Outils de test : rendu avec les mêmes fournisseurs que l'application, et faux serveur. */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { AuthProvider } from '../auth/AuthContext'

export function renderWithProviders(ui: ReactElement, { route = '/', path = '*' }: { route?: string; path?: string } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <AuthProvider>
          <Routes>
            <Route path={path} element={ui} />
            <Route path="/connexion" element={<p>Page de connexion</p>} />
            <Route path="/espace" element={<p>Espace organisateur</p>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

type Handler = (init: RequestInit | undefined, url: string) => { status?: number; body?: unknown }

/**
 * Remplace fetch par un faux serveur : chaque clé "MÉTHODE /chemin" renvoie une réponse.
 * Retourne le mock pour vérifier les appels effectués.
 */
export function mockApi(routes: Record<string, Handler | { status?: number; body?: unknown }>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const path = url.replace(/^https?:\/\/[^/]+\/api/, '').split('?')[0]
    const key = `${init?.method ?? 'GET'} ${path}`
    const route = routes[key]
    if (!route) return new Response(JSON.stringify({ detail: `Route non simulée : ${key}` }), { status: 500 })
    const { status = 200, body } = typeof route === 'function' ? route(init, url) : route
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
