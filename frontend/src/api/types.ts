/**
 * Types TypeScript qui reflètent les schémas Pydantic de l'API.
 * Ils garantissent à la compilation que le front-end lit les bons champs.
 */

// Union de chaînes : TypeScript n'accepte que ces valeurs exactes, ce qui évite les fautes de frappe.
// Statut d'un camp : brouillon, publié ou archivé.
export type CampStatus = 'draft' | 'published' | 'archived'
// Catégorie d'une modalité (condition d'âge, niveau d'études, inclus, option, autre).
export type ModalityType = 'age_restriction' | 'education_level' | 'included' | 'option' | 'other'
// Thème saisonnier de la page d'accueil du camp.
export type SeasonTheme = 'spring' | 'summer' | 'autumn' | 'winter'
// Rôles utilisateurs. super_admin et admin sont des niveaux d'administration ; les autres sont des rôles métier.
export type UserRole = 'super_admin' | 'admin' | 'sem' | 'swe' | 'ssm' | 'dc' | 'dt' | 'organizer'
// État d'un compte : actif, inactif ou désactivé.
export type UserStatus = 'active' | 'inactive' | 'disabled'
// État d'un message de contact.
export type MessageStatus = 'unread' | 'read' | 'archived'

// Une modalité d'un camp, identifiée par sa catégorie et son libellé affiché.
export interface Modality {
  type: ModalityType
  label: string
}

// Résumé de la page d'accueil d'un camp. Le | null indique que la valeur peut être absente.
export interface LandingPageSummary {
  season_theme: SeasonTheme
  hero_title: string
  hero_description: string | null
  // Date de publication au format texte (ISO), null si pas encore publiée.
  published_at: string | null
}

/** Ce qu'un visiteur voit d'un camp publié. */
// Interface : décrit la forme d'un objet. Elle n'existe qu'à la compilation et n'ajoute aucun code à l'exécution.
export interface PublicCamp {
  id: string
  name: string
  slug: string
  description: string | null
  // Dates au format texte (ISO), à convertir avant affichage.
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
// extends : Camp reprend tous les champs de PublicCamp et en ajoute de nouveaux.
export interface Camp extends PublicCamp {
  organizer_id: string
  capacity: number
  registrations_count: number
}

// Données envoyées pour créer ou modifier un camp. Pas d'id ni de compteurs, car ils sont calculés par l'API.
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

// Une inscription à un camp, telle que renvoyée par l'API.
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

// Données saisies par le visiteur pour s'inscrire. comment est optionnel (?), donc il peut être absent de l'objet.
export interface RegistrationInput {
  first_name: string
  last_name: string
  email: string
  comment?: string
}

// Message reçu via la ligne d'assistance ou le chatbot.
export interface ContactMessage {
  id: string
  camp_id: string
  name: string
  email: string
  message: string
  // Littéraux : le canal est soit la ligne d'assistance, soit le chatbot.
  channel: 'hotline' | 'chatbot'
  status: MessageStatus
  created_at: string | null
}

// Formulaire de contact envoyé par un visiteur.
export interface ContactInput {
  name: string
  email: string
  message: string
}

// Données envoyées pour enregistrer ou publier la page d'accueil d'un camp.
export interface LandingPageInput {
  season_theme: SeasonTheme
  hero_title: string
  hero_description: string | null
  // true : publier la page ; false : enregistrer seulement en brouillon.
  publish: boolean
}

// Données agrégées du tableau de bord. Le type imbriqué décrit la structure exacte de chaque bloc.
export interface DashboardSummary {
  camps: { total: number; draft: number; published: number; archived: number }
  registrations: { total: number }
  // Tableau d'objets anonymes décrivant les inscriptions les plus récentes.
  recent_registrations: Array<{
    id: string
    camp_id: string
    first_name: string
    last_name: string
    email: string
    created_at: string | null
  }>
}

// Profil de l'utilisateur connecté. Les noms et le téléphone peuvent être absents.
export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  phone_number: string | null
  role: UserRole
  status: UserStatus
  // Indique si la double authentification est activée sur le compte.
  is_2fa_enabled: boolean
}

// Données d'inscription d'un nouveau compte. phone_number est optionnel.
export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  phone_number?: string
}

// Modification du profil : tous les champs sont optionnels, on n'envoie que ce qui change.
// Pour le téléphone, null permet d'effacer la valeur.
export interface ProfileInput {
  first_name?: string
  last_name?: string
  phone_number?: string | null
}

// Données pour créer un compte depuis le panneau du super admin, avec un rôle attribué.
export interface UserInput {
  email: string
  password: string
  first_name: string
  last_name: string
  role: UserRole
}

/** Connexion en une étape (access_token) ou deux étapes si la 2FA est active (temp_token). */
// Réponse de connexion. Les champs sont nullables : une seule des deux voies est renseignée selon requires_2fa.
export interface TokenResponse {
  access_token: string | null
  token_type: string
  // Durée de validité du jeton, probablement en secondes.
  expires_in: number
  requires_2fa: boolean
  temp_token: string | null
}

// Données renvoyées lors de l'activation de la 2FA : secret à saisir et QR code à scanner.
export interface TwoFactorSetup {
  secret: string
  // Lien otpauth:// lu par les applications d'authentification.
  otpauth_url: string
  // Image du QR code encodée en base64, à afficher directement dans une balise <img>.
  qr_code_base64: string
}

// Confirmation d'envoi d'un code de vérification.
export interface VerificationSent {
  message: string
  /** Présent uniquement en développement (envoi simulé). */
  // À ne jamais afficher en production : le code ne doit normalement pas être visible.
  debug_code: string | null
}

// Format d'une sauvegarde : SQL (base complète) ou CSV (export tabulaire).
export type BackupFormat = 'sql' | 'csv'

// Une sauvegarde enregistrée, avec sa taille en kilo-octets si elle est connue.
export interface Backup {
  id: string
  format: BackupFormat
  // Identifiant de l'utilisateur qui a déclenché la sauvegarde.
  triggered_by: string
  file_size_kb: number | null
  created_at: string | null
}

// Réponse du chatbot à un message du visiteur.
export interface ChatReply {
  // Identifiant de la session de conversation, à renvoyer pour les messages suivants.
  session_id: string
  reply: string
  // Intention détectée (par exemple « prix » ou « dates »), utile pour les statistiques.
  intent: string
}

// Un message dans l'historique d'une conversation.
export interface ChatMessage {
  // Qui a écrit le message : le visiteur ou le bot.
  role: 'visitor' | 'bot'
  content: string
  // Intention détectée, uniquement pour les messages du bot (ou du visiteur si détectée). null sinon.
  intent: string | null
  // Horodatage du message.
  at: string
}

// Conversation complète avec son historique.
export interface Conversation {
  session_id: string
  // Slug du camp concerné par la conversation.
  camp_slug: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

// Statistiques globales du chatbot pour un camp.
export interface ChatStats {
  conversations: number
  visitor_messages: number
  // Les intentions les plus fréquentes, classées par nombre d'occurrences.
  top_intents: Array<{ intent: string; count: number }>
}