/**
 * Thème saisonnier de la landing page (cahier des charges : compte à rebours
 * "au style adapté à la saison"). Si l'organisateur n'a pas choisi de thème,
 * on le déduit du mois de début du camp.
 */

// Type des valeurs de saison : 'spring' | 'summer' | 'autumn' | 'winter'.
import type { SeasonTheme } from '../api/types'
// Lit une date « AAAA-MM-JJ » en heure locale (voir format.ts).
import { parseDay } from './format'

// Déduit la saison à partir d'une date « AAAA-MM-JJ ».
export function seasonFromDate(isoDate: string): SeasonTheme {
  // getMonth() renvoie 0 pour janvier, d'où le « + 1 » pour obtenir 1 à 12.
  const month = parseDay(isoDate).getMonth() + 1
  // Découpage par mois civils : printemps mars-mai, été juin-août, automne septembre-novembre.
  if (month >= 3 && month <= 5) return 'spring'
  if (month >= 6 && month <= 8) return 'summer'
  if (month >= 9 && month <= 11) return 'autumn'
  // Décembre, janvier et février restent en hiver (cas par défaut).
  return 'winter'
}

/** Classes Tailwind par saison (écrites en entier pour que Tailwind les détecte). */
// Tailwind analyse le code source pour générer les classes utilisées. Il ne reconnaît pas
// les noms construits dynamiquement (par exemple `bg-${saison}`) : on écrit donc chaque classe en entier.
export const seasonStyles: Record<SeasonTheme, { accent: string; soft: string; text: string; emoji: string }> = {
  spring: { accent: 'bg-spring', soft: 'bg-spring-soft', text: 'text-spring', emoji: '🌱' },
  summer: { accent: 'bg-summer', soft: 'bg-summer-soft', text: 'text-autumn', emoji: '☀️' },
  autumn: { accent: 'bg-autumn', soft: 'bg-autumn-soft', text: 'text-autumn', emoji: '🍂' },
  winter: { accent: 'bg-winter', soft: 'bg-winter-soft', text: 'text-winter', emoji: '❄️' },
}

// Forme du compte à rebours. « started » indique que la date est passée.
export interface Countdown {
  days: number
  hours: number
  minutes: number
  seconds: number
  started: boolean
}

/** Temps restant avant le début du camp (minuit, heure locale). */
// now est facultatif : par défaut la date actuelle, mais un test peut fournir une date fixe.
export function countdownTo(isoDate: string, now: Date = new Date()): Countdown {
  // Différence en millisecondes entre minuit le jour de début et maintenant.
  const diff = parseDay(isoDate).getTime() - now.getTime()
  // Si la date est atteinte ou dépassée, le camp a commencé : on renvoie des zéros.
  if (diff <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0, started: true }
  // Conversion en secondes entières (les millisecondes sont abandonnées).
  const totalSeconds = Math.floor(diff / 1000)
  return {
    // 86400 = secondes dans une journée (24 × 3600).
    days: Math.floor(totalSeconds / 86400),
    // Heures restantes après extraction des jours.
    hours: Math.floor((totalSeconds % 86400) / 3600),
    // Minutes restantes après extraction des heures.
    minutes: Math.floor((totalSeconds % 3600) / 60),
    // Secondes restantes après extraction des minutes.
    seconds: totalSeconds % 60,
    started: false,
  }
}