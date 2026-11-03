import { describe, expect, it } from 'vitest'
import { campSchema } from './campSchema'
import { formatAge, formatRange, parseDay } from './format'
import { countdownTo, seasonFromDate } from './season'

describe('dates', () => {
  it('lit une date de l’API en heure locale (pas de décalage UTC)', () => {
    const day = parseDay('2026-07-01')
    expect([day.getFullYear(), day.getMonth(), day.getDate()]).toEqual([2026, 6, 1])
  })

  it('formate une période en français', () => {
    expect(formatRange('2026-07-06', '2026-07-17')).toBe('du 6 juil. au 17 juillet 2026')
  })

  it("formate l'âge minimum", () => {
    expect(formatAge(12)).toBe('À partir de 12 ans')
    expect(formatAge(null)).toBe('Tous âges')
  })
})

describe('saisons et compte à rebours', () => {
  it.each([
    ['2026-04-10', 'spring'],
    ['2026-07-06', 'summer'],
    ['2026-10-20', 'autumn'],
    ['2026-12-28', 'winter'],
    ['2027-01-15', 'winter'],
  ])('%s -> %s', (date, season) => {
    expect(seasonFromDate(date)).toBe(season)
  })

  it('calcule le temps restant', () => {
    const now = new Date(2026, 6, 4, 22, 30, 15) // 4 juillet 2026, 22:30:15
    expect(countdownTo('2026-07-06', now)).toEqual({ days: 1, hours: 1, minutes: 29, seconds: 45, started: false })
  })

  it('indique quand le camp a commencé', () => {
    expect(countdownTo('2026-07-06', new Date(2026, 6, 7)).started).toBe(true)
  })
})

describe('validation du formulaire de camp', () => {
  const valid = {
    name: 'Code Explorers',
    description: '',
    start_date: '2026-07-06',
    end_date: '2026-07-17',
    city: 'Lyon',
    age: 12,
    capacity: 24,
    status: 'draft' as const,
    modalities: [],
  }

  it('accepte un camp valide', () => {
    expect(campSchema.safeParse(valid).success).toBe(true)
  })

  it('refuse une fin avant le début', () => {
    const result = campSchema.safeParse({ ...valid, end_date: '2026-07-01' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toEqual(['end_date'])
  })

  it('accepte un camp ouvert à tous les âges (age null)', () => {
    expect(campSchema.safeParse({ ...valid, age: null }).success).toBe(true)
  })

  it('refuse un âge invalide', () => {
    const result = campSchema.safeParse({ ...valid, age: 150 })
    expect(result.error?.issues[0].path).toEqual(['age'])
  })

  it('refuse une capacité nulle', () => {
    expect(campSchema.safeParse({ ...valid, capacity: 0 }).success).toBe(false)
  })
})
