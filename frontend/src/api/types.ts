/**
 * Types TypeScript qui reflètent les schémas Pydantic de l'API.
 * Ils garantissent à la compilation que le front-end lit les bons champs.
 */

export type CampStatus = 'draft' | 'published' | 'archived'
export type ModalityType = 'age_restriction' | 'education_level' | 'included' | 'option' | 'other'
export type SeasonTheme = 'spring' | 'summer' | 'autumn' | 'winter'
export type UserRole = 'super_admin' | 'admin' | 'sem' | 'swe' | 'ssm' | 'dc' | 'dt' | 'organizer'
export type UserStatus = 'active' | 'inactive' | 'disabled'
export type MessageStatus = 'unread' | 'read' | 'archived'

export interface Modality {
  type: ModalityType
  label: string
}

export interface LandingPageSummary {
  season_theme: SeasonTheme
  hero_title: string
  hero_description: string | null
  published_at: string | null
}

/** Ce qu'un visiteur voit d'un camp publié. */
export interface PublicCamp {
  id: string
  name: string
  slug: string
  description: string | null
  start_date: string
  end_date: string
  city: string
  /** Âge minimum requis ; null = tous âges. */
  age: number | null
  status: CampStatus
  remaining_places: number
  modalities: Modality[]
  landing_page: LandingPageSummary | null
}

/** Vue organisateur : ajoute les champs internes. */
export interface Camp extends PublicCamp {
  organizer_id: string
  capacity: number
  registrations_count: number
}

export interface CampInput {
  name: string
  description: string | null
  start_date: string
  end_date: string
  city: string
  age: number | null
  capacity: number
  status: CampStatus
  modalities: Modality[]
}

export interface Registration {
  id: string
  camp_id: string
  first_name: string
  last_name: string
  email: string
  comment: string | null
  confirmed: boolean
  created_at: string | null
}

export interface RegistrationInput {
  first_name: string
  last_name: string
  email: string
  comment?: string
}

export interface ContactMessage {
  id: string
  camp_id: string
  name: string
  email: string
  message: string
  channel: 'hotline' | 'chatbot'
  status: MessageStatus
  created_at: string | null
}

export interface ContactInput {
  name: string
  email: string
  message: string
}

export interface LandingPageInput {
  season_theme: SeasonTheme
  hero_title: string
  hero_description: string | null
  publish: boolean
}

export interface DashboardSummary {
  camps: { total: number; draft: number; published: number; archived: number }
  registrations: { total: number }
  recent_registrations: Array<{
    id: string
    camp_id: string
    first_name: string
    last_name: string
    email: string
    created_at: string | null
  }>
}

export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  phone_number: string | null
  role: UserRole
  status: UserStatus
  is_2fa_enabled: boolean
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  phone_number?: string
}

export interface ProfileInput {
  first_name?: string
  last_name?: string
  phone_number?: string | null
}

export interface UserInput {
  email: string
  password: string
  first_name: string
  last_name: string
  role: UserRole
}

/** Connexion en une étape (access_token) ou deux étapes si la 2FA est active (temp_token). */
export interface TokenResponse {
  access_token: string | null
  token_type: string
  expires_in: number
  requires_2fa: boolean
  temp_token: string | null
}

export interface TwoFactorSetup {
  secret: string
  otpauth_url: string
  qr_code_base64: string
}

export interface VerificationSent {
  message: string
  /** Présent uniquement en développement (envoi simulé). */
  debug_code: string | null
}

export type BackupFormat = 'sql' | 'csv'

export interface Backup {
  id: string
  format: BackupFormat
  triggered_by: string
  file_size_kb: number | null
  created_at: string | null
}

export interface ChatReply {
  session_id: string
  reply: string
  intent: string
}

export interface ChatMessage {
  role: 'visitor' | 'bot'
  content: string
  intent: string | null
  at: string
}

export interface Conversation {
  session_id: string
  camp_slug: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

export interface ChatStats {
  conversations: number
  visitor_messages: number
  top_intents: Array<{ intent: string; count: number }>
}
