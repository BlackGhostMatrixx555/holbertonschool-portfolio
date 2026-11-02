/** Fonctions d'affichage partagées (dates en français, libellés). */
import type { CampStatus, MessageStatus, ModalityType, SeasonTheme, UserRole, UserStatus } from '../api/types'

/**
 * Lit une date "AAAA-MM-JJ" de l'API comme une date LOCALE.
 * new Date("2026-07-01") la lirait en UTC et pourrait afficher le 30 juin.
 */
export function parseDay(value: string): Date {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  return new Date(year, month - 1, day)
}

const dayFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
const shortFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })
const dateTimeFormat = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' })

export const formatDay = (value: string) => dayFormat.format(parseDay(value))
export const formatDateTime = (value: string | null) => (value ? dateTimeFormat.format(new Date(value)) : '–')

export function formatRange(start: string, end: string): string {
  return `du ${shortFormat.format(parseDay(start))} au ${dayFormat.format(parseDay(end))}`
}

export function formatAges(min: number, max: number): string {
  if (min === 0 && max === 0) return 'Tous âges'
  return min === max ? `${min} ans` : `${min} à ${max} ans`
}

export const statusLabels: Record<CampStatus, string> = {
  draft: 'Brouillon',
  published: 'Publié',
  archived: 'Archivé',
}

export const modalityLabels: Record<ModalityType, string> = {
  age_restriction: 'Âge',
  education_level: 'Niveau',
  included: 'Inclus',
  option: 'Option',
  other: 'Autre',
}

export const seasonLabels: Record<SeasonTheme, string> = {
  spring: 'Printemps',
  summer: 'Été',
  autumn: 'Automne',
  winter: 'Hiver',
}

export const roleLabels: Record<UserRole, string> = {
  super_admin: 'Super admin',
  admin: 'Admin',
  sem: 'SEM',
  swe: 'SWE',
  ssm: 'SSM',
  dc: 'Directeur de campus',
  organizer: 'Organisateur',
}

export const userStatusLabels: Record<UserStatus, string> = {
  active: 'Actif',
  inactive: 'Inactif',
  disabled: 'Désactivé',
}

export const messageStatusLabels: Record<MessageStatus, string> = {
  unread: 'Non lu',
  read: 'Lu',
  archived: 'Archivé',
}

export const intentLabels: Record<string, string> = {
  dates: 'Dates',
  location: 'Lieu',
  age: 'Âge / conditions',
  places: 'Places restantes',
  registration: 'Inscription',
  program: 'Programme',
  human: 'Contact humain',
  greeting: 'Salutation',
  unknown: 'Non compris',
}
