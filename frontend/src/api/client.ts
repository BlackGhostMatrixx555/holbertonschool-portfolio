/**
 * Client HTTP unique pour toute l'application.
 *
 * - Préfixe chaque appel par l'URL de l'API (variable VITE_API_URL).
 * - Ajoute l'en-tête "Authorization: Bearer <jeton>" quand l'utilisateur est connecté.
 * - Transforme les erreurs FastAPI en ApiError avec un message lisible.
 * - Prévient l'application quand le jeton est refusé (401), pour déconnecter l'utilisateur.
 */

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let authToken: string | null = null
let onUnauthorized: (() => void) | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

/** Erreur de validation FastAPI : { detail: [{ loc, msg }] } */
interface ValidationIssue {
  loc?: Array<string | number>
  msg?: string
}

/**
 * FastAPI renvoie soit { detail: "message" }, soit { detail: [ {loc, msg}, ... ] }
 * pour les erreurs 422. On en fait une phrase affichable.
 */
export function formatErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = (detail as ValidationIssue[])
      .map((issue) => {
        const field = issue.loc?.filter((part) => part !== 'body').join('.')
        const message = (issue.msg ?? '').replace(/^Value error, /, '')
        return field ? `${field} : ${message}` : message
      })
      .filter(Boolean)
    if (messages.length > 0) return messages.join(' · ')
  }
  return fallback
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
}

async function send(path: string, { method = 'GET', body, signal }: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (authToken) headers.Authorization = `Bearer ${authToken}`

  let response: Response
  try {
    response = await fetch(`${API_URL}/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Impossible de joindre le serveur. Vérifiez votre connexion.')
  }

  if (!response.ok) {
    if (response.status === 401 && authToken && onUnauthorized) onUnauthorized()
    let detail: unknown = null
    try {
      detail = (await response.json()).detail
    } catch {
      /* corps vide ou non JSON */
    }
    throw new ApiError(response.status, formatErrorDetail(detail, `Erreur ${response.status}`))
  }
  return response
}

/** Requête JSON : retourne le corps décodé (ou undefined pour une réponse 204). */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/** Requête qui retourne un fichier (export de sauvegarde). */
export async function requestBlob(path: string): Promise<{ blob: Blob; filename: string }> {
  const response = await send(path, {})
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const match = /filename="?([^";]+)"?/i.exec(disposition)
  return { blob: await response.blob(), filename: match?.[1] ?? 'camporga-backup' }
}
