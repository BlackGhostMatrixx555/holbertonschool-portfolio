/**
 * Client HTTP unique pour toute l'application.
 *
 * - Préfixe chaque appel par l'URL de l'API (variable VITE_API_URL).
 * - Ajoute l'en-tête "Authorization: Bearer <jeton>" quand l'utilisateur est connecté.
 * - Transforme les erreurs FastAPI en ApiError avec un message lisible.
 * - Prévient l'application quand le jeton est refusé (401), pour déconnecter l'utilisateur.
 */

// Adresse de base de l'API. import.meta.env lit les variables définies par Vite (fichier .env).
// L'opérateur ?? fournit une valeur par défaut si la variable n'est pas définie.
export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Erreur propre à l'API. Elle hérite de Error, ce qui permet de la distinguer des autres erreurs.
export class ApiError extends Error {
  // Code HTTP (400, 401, 404, 422, 500...). 0 signifie que le serveur est injoignable.
  readonly status: number

  constructor(status: number, message: string) {
    // super() appelle le constructeur d'Error avec le message.
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// Variables de module : partagées par toutes les requêtes, mais invisibles depuis l'extérieur.
// Jeton courant, ajouté à chaque requête authentifiée. null si personne n'est connecté.
let authToken: string | null = null
// Fonction appelée lors d'un 401, fournie par le contexte d'authentification.
let onUnauthorized: (() => void) | null = null

// Enregistre (ou efface, avec null) le jeton utilisé dans les prochaines requêtes.
export function setAuthToken(token: string | null): void {
  authToken = token
}

// Enregistre le gestionnaire appelé en cas de 401. Passer null le désactive.
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

/** Erreur de validation FastAPI : { detail: [{ loc, msg }] } */
// Forme d'un élément de la liste d'erreurs. Les champs sont optionnels (?) car FastAPI peut les omettre.
interface ValidationIssue {
  // Chemin vers le champ fautif, par exemple ["body", "email"]. Les nombres désignent un index de tableau.
  loc?: Array<string | number>
  msg?: string
}

/**
 * FastAPI renvoie soit { detail: "message" }, soit { detail: [ {loc, msg}, ... ] }
 * pour les erreurs 422. On en fait une phrase affichable.
 */
// export : fonction exportée pour pouvoir être testée ou réutilisée. unknown force à vérifier le type avant usage.
export function formatErrorDetail(detail: unknown, fallback: string): string {
  // Cas simple : FastAPI a renvoyé un message texte.
  if (typeof detail === 'string') return detail
  // Cas des erreurs de validation : on transforme chaque erreur en phrase.
  if (Array.isArray(detail)) {
    const messages = (detail as ValidationIssue[])
      .map((issue) => {
        // On retire "body" du chemin (sans intérêt pour l'utilisateur), puis on joint les morceaux par un point.
        const field = issue.loc?.filter((part) => part !== 'body').join('.')
        // Retire le préfixe "Value error, " ajouté par Pydantic aux erreurs de validation personnalisées.
        const message = (issue.msg ?? '').replace(/^Value error, /, '')
        return field ? `${field} : ${message}` : message
      })
      // Supprime les entrées vides (filter sur une chaîne vide retourne false).
      .filter(Boolean)
    // Si au moins un message existe, on les réunit avec un séparateur.
    if (messages.length > 0) return messages.join(' · ')
  }
  // Aucun format reconnu : on retourne le message par défaut.
  return fallback
}

// Options acceptées par les fonctions de requête. Toutes sont facultatives (?).
interface RequestOptions {
  // Type union : seules ces valeurs HTTP sont acceptées.
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  // Corps de la requête, de type inconnu car il dépend de l'appel.
  body?: unknown
  // Permet d'annuler la requête (par exemple quand le composant est démonté).
  signal?: AbortSignal
}

// Fonction interne qui fait l'envoi réel. Elle n'est pas exportée : seules request et requestBlob l'utilisent.
// = { method = 'GET', ... } : déstructuration avec valeur par défaut pour method.
async function send(path: string, { method = 'GET', body, signal }: RequestOptions): Promise<Response> {
  // Objet des en-têtes HTTP, construit au fur et à mesure.
  const headers: Record<string, string> = {}
  // Le type JSON n'est déclaré que s'il y a un corps à envoyer.
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  // Ajoute le jeton si l'utilisateur est connecté (la chaîne vide et null sont considérées fausses).
  if (authToken) headers.Authorization = `Bearer ${authToken}`

  let response: Response
  try {
    // Appel réseau. Les chemins reçus commencent par "/", on ajoute donc le préfixe /api.
    response = await fetch(`${API_URL}/api${path}`, {
      method,
      headers,
      // Le corps est converti en texte JSON. Sans corps, on envoie undefined.
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    // Une annulation volontaire n'est pas une erreur réseau : on la relance telle quelle.
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    // Échec de fetch (serveur arrêté, pas de réseau, CORS...) : on le signale avec le statut 0.
    throw new ApiError(0, 'Impossible de joindre le serveur. Vérifiez votre connexion.')
  }

  // Statut 2xx = succès. Sinon, on construit une erreur.
  if (!response.ok) {
    // Un 401 avec un jeton enregistré signifie que la session n'est plus valide : on déconnecte.
    if (response.status === 401 && authToken && onUnauthorized) onUnauthorized()
    let detail: unknown = null
    try {
      // Lit le corps JSON pour récupérer le champ "detail" renvoyé par FastAPI.
      detail = (await response.json()).detail
    } catch {
      /* corps vide ou non JSON : on garde detail à null */
    }
    throw new ApiError(response.status, formatErrorDetail(detail, `Erreur ${response.status}`))
  }
  return response
}

/** Requête JSON : retourne le corps décodé (ou undefined pour une réponse 204). */
// <T> : paramètre de type générique. L'appelant indique le type attendu, par exemple request<User>(...).
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options)
  // 204 No Content : aucun corps à lire.
  if (response.status === 204) return undefined as T
  // "as T" : l'affirmation de type ne vérifie rien à l'exécution, la donnée est supposée conforme.
  return (await response.json()) as T
}

/** Requête qui retourne un fichier (export de sauvegarde). */
// Renvoie le fichier binaire et son nom, extrait de l'en-tête Content-Disposition.
export async function requestBlob(path: string): Promise<{ blob: Blob; filename: string }> {
  const response = await send(path, {})
  // Lit l'en-tête qui contient le nom du fichier. ?? '' évite une erreur si l'en-tête est absent.
  const disposition = response.headers.get('Content-Disposition') ?? ''
  // Expression régulière : capture le nom entre guillemets optionnels. i : insensible à la casse.
  const match = /filename="?([^";]+)"?/i.exec(disposition)
  // Nom de repli si l'en-tête est absent ou mal formé.
  return { blob: await response.blob(), filename: match?.[1] ?? 'camporga-backup' }
}