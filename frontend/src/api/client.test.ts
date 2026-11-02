import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockApi } from '../test/utils'
import { ApiError, formatErrorDetail, request, setAuthToken, setUnauthorizedHandler } from './client'

afterEach(() => {
  setAuthToken(null)
  setUnauthorizedHandler(null)
  vi.unstubAllGlobals()
})

describe('formatErrorDetail', () => {
  it('garde un message simple tel quel', () => {
    expect(formatErrorDetail('Camp introuvable.', 'x')).toBe('Camp introuvable.')
  })

  it('met en forme les erreurs de validation FastAPI (422)', () => {
    const detail = [{ loc: ['body', 'end_date'], msg: 'Value error, end_date doit être supérieure ou égale à start_date' }]
    expect(formatErrorDetail(detail, 'x')).toBe('end_date : end_date doit être supérieure ou égale à start_date')
  })

  it('utilise le message par défaut sinon', () => {
    expect(formatErrorDetail(null, 'Erreur 500')).toBe('Erreur 500')
  })
})

describe('request', () => {
  it("ajoute le jeton dans l'en-tête Authorization", async () => {
    const fetchMock = mockApi({ 'GET /auth/me': { body: { id: '1' } } })
    setAuthToken('abc')
    await request('/auth/me')
    const headers = fetchMock.mock.calls[0][1]?.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer abc')
  })

  it('lève une ApiError avec le message de l’API', async () => {
    mockApi({ 'GET /camps/x/public': { status: 404, body: { detail: 'Camp introuvable.' } } })
    await expect(request('/camps/x/public')).rejects.toEqual(new ApiError(404, 'Camp introuvable.'))
  })

  it('prévient l’application quand le jeton est refusé (401)', async () => {
    mockApi({ 'GET /camps': { status: 401, body: { detail: 'Token invalide ou expiré.' } } })
    const onUnauthorized = vi.fn()
    setAuthToken('expired')
    setUnauthorizedHandler(onUnauthorized)
    await expect(request('/camps')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })

  it('traduit une panne réseau en message lisible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(request('/public/camps')).rejects.toMatchObject({ status: 0 })
  })
})
