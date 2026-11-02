/**
 * Une fonction par route de l'API. Les composants n'écrivent jamais d'URL
 * eux-mêmes : si une route change, on ne modifie que ce fichier.
 */
import { request, requestBlob } from './client'
import type {
  Camp,
  CampInput,
  ChatReply,
  ChatStats,
  ContactInput,
  ContactMessage,
  Conversation,
  DashboardSummary,
  LandingPageInput,
  MessageStatus,
  PublicCamp,
  Registration,
  RegistrationInput,
  TokenResponse,
  User,
  UserInput,
  UserRole,
  UserStatus,
} from './types'

const enc = encodeURIComponent

// ---- Authentification --------------------------------------------------------
export const login = (email: string, password: string) =>
  request<TokenResponse>('/auth/login', { method: 'POST', body: { email, password } })
export const fetchMe = () => request<User>('/auth/me')

// ---- Public ------------------------------------------------------------------
export const fetchPublicCamps = () => request<PublicCamp[]>('/public/camps')
export const fetchPublicCamp = (slug: string) => request<PublicCamp>(`/camps/${enc(slug)}/public`)
export const registerToCamp = (slug: string, body: RegistrationInput) =>
  request<Registration>(`/camps/${enc(slug)}/registrations`, { method: 'POST', body })
export const sendContactMessage = (slug: string, body: ContactInput) =>
  request<ContactMessage>(`/camps/${enc(slug)}/contact-messages`, { method: 'POST', body })
export const sendChatMessage = (slug: string, message: string, sessionId: string | null) =>
  request<ChatReply>(`/camps/${enc(slug)}/chat`, {
    method: 'POST',
    body: sessionId ? { message, session_id: sessionId } : { message },
  })

// ---- Organisateur ------------------------------------------------------------
export const fetchDashboard = () => request<DashboardSummary>('/dashboard/summary')
export const fetchCamps = () => request<Camp[]>('/camps')
export const fetchCamp = (id: string) => request<Camp>(`/camps/${enc(id)}`)
export const createCamp = (body: CampInput) => request<Camp>('/camps', { method: 'POST', body })
export const updateCamp = (id: string, body: Partial<CampInput>) =>
  request<Camp>(`/camps/${enc(id)}`, { method: 'PATCH', body })
export const deleteCamp = (id: string) => request<void>(`/camps/${enc(id)}`, { method: 'DELETE' })

export const saveLandingPage = (campId: string, body: LandingPageInput) =>
  request(`/camps/${enc(campId)}/landing-page`, { method: 'PUT', body })

export const fetchRegistrations = (campId: string) =>
  request<Registration[]>(`/camps/${enc(campId)}/registrations`)
export const setAttendance = (registrationId: string, confirmed: boolean) =>
  request<Registration>(`/registrations/${enc(registrationId)}/attendance`, {
    method: 'PATCH',
    body: { confirmed },
  })

export const fetchMessages = (campId: string) =>
  request<ContactMessage[]>(`/camps/${enc(campId)}/contact-messages`)
export const setMessageStatus = (messageId: string, status: MessageStatus) =>
  request<ContactMessage>(`/contact-messages/${enc(messageId)}`, { method: 'PATCH', body: { status } })

export const fetchChatStats = (campId: string) => request<ChatStats>(`/camps/${enc(campId)}/chat/stats`)
export const fetchConversations = (campId: string) =>
  request<Conversation[]>(`/camps/${enc(campId)}/chat/conversations?limit=20`)

// ---- Super admin -------------------------------------------------------------
export const fetchUsers = () => request<User[]>('/users')
export const createUser = (body: UserInput) => request<User>('/users', { method: 'POST', body })
export const setUserRole = (id: string, role: UserRole) =>
  request<User>(`/users/${enc(id)}/role`, { method: 'PATCH', body: { role } })
export const setUserStatus = (id: string, status: UserStatus) =>
  request<User>(`/users/${enc(id)}/status`, { method: 'PATCH', body: { status } })
export const downloadBackup = (format: 'csv' | 'sql') => requestBlob(`/admin/backups?format=${format}`)
