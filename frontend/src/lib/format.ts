/** Fonctions d'affichage partagées (dates en français, libellés). */

// Types des valeurs possibles pour chaque champ (statuts, rôles, thèmes…).
// Ils garantissent que chaque libellé couvre bien toutes les valeurs de l'API.
import type { CampStatus, MessageStatus, ModalityType, SeasonTheme, UserRole, UserStatus } from '../api/types'

/**
 * Lit une date "AAAA-MM-JJ" de l'API comme une date LOCALE.
 * new Date("2026-07-01") la lirait en UTC et pourrait afficher le 30 juin.
 */
export function parseDay(value: string): Date {
  // slice(0, 10) : garde uniquement la partie date si la valeur contient une heure.
  // split/map(Number) : transforme "2026-07-01" en [2026, 7, 1].
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  // Le mois est indexé à partir de 0 dans le constructeur Date, d'où le « - 1 ».
  return new Date(year, month - 1, day)
}

// Formateurs réutilisables, créés une seule fois (plus performant que de les recréer à chaque appel).
// Exemple : « 1 juillet 2026 ».
const dayFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
// Exemple : « 1 juil. ».
const shortFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })
// Exemple : « 01/07/2026 14:30 ».
const dateTimeFormat = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' })

// Affiche une date « AAAA-MM-JJ » au format long.
export const formatDay = (value: string) => dayFormat.format(parseDay(value))

// Affiche une date-heure complète, ou un tiret si la valeur est absente.
export const formatDateTime = (value: string | null) => (value ? dateTimeFormat.format(new Date(value)) : '–')

// Affiche une période : « du 1 juil. au 15 juil. 2026 ».
export function formatRange(start: string, end: string): string {
  return `du ${shortFormat.format(parseDay(start))} au ${dayFormat.format(parseDay(end))}`
}

/** Âge minimum requis : "À partir de 12 ans", ou "Tous âges" si non précisé. */
export function formatAge(age: number | null): string {
  // 0 et null signifient tous deux « sans restriction d'âge ».
  return age === null || age === 0 ? 'Tous âges' : `À partir de ${age} ans`
}

// Libellés des statuts de camp.
export const statusLabels: Record<CampStatus, string> = {
  draft: 'Brouillon',
  published: 'Publié',
  archived: 'Archivé',
}

// Libellés des types de modalités (conditions, options, inclusions).
export const modalityLabels: Record<ModalityType, string> = {
  age_restriction: 'Âge',
  education_level: 'Niveau',
  included: 'Inclus',
  option: 'Option',
  other: 'Autre',
}

// Libellés des saisons.
export const seasonLabels: Record<SeasonTheme, string> = {
  spring: 'Printemps',
  summer: 'Été',
  autumn: 'Automne',
  winter: 'Hiver',
}

// Libellés des rôles. Utilisés dans les listes et les formulaires de la page Utilisateurs.
export const roleLabels: Record<UserRole, string> = {
  super_admin: 'Super admin',
  admin: 'Admin',
  sem: 'SEM',
  swe: 'SWE',
  ssm: 'SSM',
  dc: 'Directeur de campus',
  dt: 'Directeur technique',
  organizer: 'Organisateur',
}

// Libellés des statuts de compte.
export const userStatusLabels: Record<UserStatus, string> = {
  active: 'Actif',
  inactive: 'Inactif',
  disabled: 'Désactivé',
}

// Libellés des statuts de message.
export const messageStatusLabels: Record<MessageStatus, string> = {
  unread: 'Non lu',
  read: 'Lu',
  archived: 'Archivé',
}

// Libellés des intentions détectées par le chatbot. Type Record<string, string> :
// pas de vérification de couverture, contrairement aux autres libellés.
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