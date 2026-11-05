/**
 * Thème saisonnier de la landing page (cahier des charges : compte à rebours
 * "au style adapté à la saison"). Si l'organisateur n'a pas choisi de thème,
 * on le déduit du mois de début du camp.
 */
import type { SeasonTheme } from '../api/types'
import { parseDay } from './format'

export function seasonFromDate(isoDate: string): SeasonTheme {
  const month = parseDay(isoDate).getMonth() + 1
  if (month >= 3 && month <= 5) return 'spring'
  if (month >= 6 && month <= 8) return 'summer'
  if (month >= 9 && month <= 11) return 'autumn'
  return 'winter'
}

/** Classes Tailwind par saison (écrites en entier pour que Tailwind les détecte). */
export const seasonStyles: Record<SeasonTheme, { accent: string; soft: string; text: string; emoji: string }> = {
  spring: { accent: 'bg-spring', soft: 'bg-spring-soft', text: 'text-spring', emoji: '🌱' },
  summer: { accent: 'bg-summer', soft: 'bg-summer-soft', text: 'text-autumn', emoji: '☀️' },
  autumn: { accent: 'bg-autumn', soft: 'bg-autumn-soft', text: 'text-autumn', emoji: '🍂' },
  winter: { accent: 'bg-winter', soft: 'bg-winter-soft', text: 'text-winter', emoji: '❄️' },
}

export interface Countdown {
  days: number
  hours: number
  minutes: number
  seconds: number
  started: boolean
}

/** Temps restant avant le début du camp (minuit, heure locale). */
export function countdownTo(isoDate: string, now: Date = new Date()): Countdown {
  const diff = parseDay(isoDate).getTime() - now.getTime()
  if (diff <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0, started: true }
  const totalSeconds = Math.floor(diff / 1000)
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    started: false,
  }
}
