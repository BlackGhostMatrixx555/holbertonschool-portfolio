// describe, it, expect : fonctions de Vitest (framework de tests).
// describe regroupe des tests, it décrit un cas, expect vérifie un résultat.
import { describe, expect, it } from 'vitest'

// Fonctions testées : schéma de validation, formatage, saison et compte à rebours.
import { campSchema } from './campSchema'
import { formatAge, formatRange, parseDay } from './format'
import { countdownTo, seasonFromDate } from './season'

// ---- Dates et formatage ------------------------------------------------------

describe('dates', () => {
  it('lit une date de l’API en heure locale (pas de décalage UTC)', () => {
    const day = parseDay('2026-07-01')
    // Vérifie année, mois (indexé à partir de 0 : juillet = 6) et jour, sans passer par UTC.
    expect([day.getFullYear(), day.getMonth(), day.getDate()]).toEqual([2026, 6, 1])
  })

  it('formate une période en français', () => {
    // Le début est en format court (« 6 juil. »), la fin en format long avec l'année.
    expect(formatRange('2026-07-06', '2026-07-17')).toBe('du 6 juil. au 17 juillet 2026')
  })

  it("formate l'âge minimum", () => {
    expect(formatAge(12)).toBe('À partir de 12 ans')
    expect(formatAge(null)).toBe('Tous âges')
  })
})

// ---- Saisons et compte à rebours ---------------------------------------------

describe('saisons et compte à rebours', () => {
  // it.each : exécute le même test pour chaque ligne du tableau.
  // %s est remplacé par les valeurs de la ligne dans le nom du test.
  it.each([
    ['2026-04-10', 'spring'],
    ['2026-07-06', 'summer'],
    ['2026-10-20', 'autumn'],
    ['2026-12-28', 'winter'],
    ['2027-01-15', 'winter'], // janvier appartient à l'hiver de la même année civile
  ])('%s -> %s', (date, season) => {
    expect(seasonFromDate(date)).toBe(season)
  })

  it('calcule le temps restant', () => {
    // Date « figée » passée en paramètre : le résultat ne dépend pas de l'horloge réelle.
    const now = new Date(2026, 6, 4, 22, 30, 15) // 4 juillet 2026, 22:30:15
    // Du 4 juillet 22:30:15 au 6 juillet 00:00 : 1 jour, 1 h 29 min 45 s.
    expect(countdownTo('2026-07-06', now)).toEqual({ days: 1, hours: 1, minutes: 29, seconds: 45, started: false })
  })

  it('indique quand le camp a commencé', () => {
    // Le 7 juillet est après le 6 : le camp a déjà commencé.
    expect(countdownTo('2026-07-06', new Date(2026, 6, 7)).started).toBe(true)
  })
})

// ---- Validation du formulaire ------------------------------------------------

describe('validation du formulaire de camp', () => {
  // Jeu de données valide servant de base. Chaque test modifie un seul champ.
  const valid = {
    name: 'Code Explorers',
    description: '',
    start_date: '2026-07-06',
    end_date: '2026-07-17',
    city: 'Lyon',
    age: 12,
    capacity: 24,
    status: 'draft' as const, // « as const » fixe le type littéral attendu par le schéma
    modalities: [],
  }

  it('accepte un camp valide', () => {
    expect(campSchema.safeParse(valid).success).toBe(true)
  })

  it('refuse une fin avant le début', () => {
    const result = campSchema.safeParse({ ...valid, end_date: '2026-07-01' })
    expect(result.success).toBe(false)
    // Vérifie que l'erreur est bien rattachée au champ end_date.
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