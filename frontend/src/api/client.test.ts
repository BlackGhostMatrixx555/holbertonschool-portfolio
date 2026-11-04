// Importe les fonctions de test de Vitest. describe regroupe les tests, it définit un test, expect vérifie un résultat.
// afterEach : code exécuté après chaque test. vi : utilitaires de simulation (mock, spy).
import { afterEach, describe, expect, it, vi } from 'vitest'
// Faux serveur défini dans les outils de test (voir l'extrait précédent).
import { mockApi } from '../test/utils'
import { ApiError, formatErrorDetail, request, setAuthToken, setUnauthorizedHandler } from './client'

// Réinitialise l'état partagé du module après chaque test pour que les tests restent indépendants.
afterEach(() => {
  setAuthToken(null)
  setUnauthorizedHandler(null)
  // Restaure les vraies fonctions globales (par exemple fetch) remplacées par vi.stubGlobal.
  vi.unstubAllGlobals()
})

// Regroupe les tests de la fonction formatErrorDetail.
describe('formatErrorDetail', () => {
  it('garde un message simple tel quel', () => {
    // Cas 1 : un texte reçu est renvoyé sans modification. Le 'x' est le repli, il ne doit pas être utilisé ici.
    expect(formatErrorDetail('Camp introuvable.', 'x')).toBe('Camp introuvable.')
  })

  it('met en forme les erreurs de validation FastAPI (422)', () => {
    // Simule une réponse 422 : la liste d'erreurs telle que la renvoie Pydantic.
    const detail = [{ loc: ['body', 'end_date'], msg: 'Value error, end_date doit être supérieure ou égale à start_date' }]
    // Vérifie la transformation : "body" retiré, préfixe "Value error, " retiré, champ suivi de " : ".
    expect(formatErrorDetail(detail, 'x')).toBe('end_date : end_date doit être supérieure ou égale à start_date')
  })

  it('utilise le message par défaut sinon', () => {
    // Cas sans détail exploitable (null) : le message de repli est renvoyé.
    expect(formatErrorDetail(null, 'Erreur 500')).toBe('Erreur 500')
  })
})

// Regroupe les tests de la fonction request.
describe('request', () => {
  it("ajoute le jeton dans l'en-tête Authorization", async () => {
    // Le faux serveur répond 200 avec un utilisateur. fetchMock enregistre chaque appel.
    const fetchMock = mockApi({ 'GET /auth/me': { body: { id: '1' } } })
    setAuthToken('abc')
    await request('/auth/me')
    // fetchMock.mock.calls[0] est le premier appel ; [1] désigne ses options. Le cast indique la forme des en-têtes.
    const headers = fetchMock.mock.calls[0][1]?.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer abc')
  })

  it('lève une ApiError avec le message de l’API', async () => {
    // Le serveur répond 404 avec un message.
    mockApi({ 'GET /camps/x/public': { status: 404, body: { detail: 'Camp introuvable.' } } })
    // rejects : vérifie que la promesse est rejetée. toEqual compare les champs de l'erreur (status et message).
    await expect(request('/camps/x/public')).rejects.toEqual(new ApiError(404, 'Camp introuvable.'))
  })

  it('prévient l’application quand le jeton est refusé (401)', async () => {
    // Le serveur refuse le jeton.
    mockApi({ 'GET /camps': { status: 401, body: { detail: 'Token invalide ou expiré.' } } })
    // Fonction espion : elle enregistre ses appels sans rien faire.
    const onUnauthorized = vi.fn()
    setAuthToken('expired')
    setUnauthorizedHandler(onUnauthorized)
    // L'erreur doit être une ApiError, et le gestionnaire doit avoir été appelé une seule fois.
    await expect(request('/camps')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })

  it('traduit une panne réseau en message lisible', async () => {
    // Remplace fetch globalement : il échoue comme le fait un réseau coupé.
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    // toMatchObject vérifie seulement que le statut vaut 0, sans comparer le message entier.
    await expect(request('/public/camps')).rejects.toMatchObject({ status: 0 })
  })
})