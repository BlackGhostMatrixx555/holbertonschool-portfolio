/**
 * Une fonction par route de l'API. Les composants n'écrivent jamais d'URL
 * eux-mêmes : si une route change, on ne modifie que ce fichier.
 */
// request : appel JSON ; requestBlob : appel qui renvoie un fichier binaire (téléchargement).
import { request, requestBlob } from './client'
// import type : seuls les types sont importés, ils disparaissent à la compilation.
import type {
  Backup,
  BackupFormat,
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
  ProfileInput,
  PublicCamp,
  RegisterInput,
  Registration,
  RegistrationInput,
  TokenResponse,
  TwoFactorSetup,
  User,
  UserInput,
  UserRole,
  UserStatus,
  VerificationSent,
} from './types'

// Raccourci pour encoder un segment d'URL (espaces, caractères spéciaux) et éviter les URL cassées ou détournées.
const enc = encodeURIComponent

// ---- Authentification --------------------------------------------------------
// Étape 1 de connexion : e-mail et mot de passe. Renvoie un jeton ou un jeton temporaire si la 2FA est active.
export const login = (email: string, password: string) =>
  request<TokenResponse>('/auth/login', { method: 'POST', body: { email, password } })
// Étape 2 de connexion : échange le jeton temporaire et le code à 6 chiffres contre un jeton de session.
export const loginTwoFactor = (tempToken: string, code: string) =>
  request<TokenResponse>('/auth/2fa/login', { method: 'POST', body: { temp_token: tempToken, code } })
// Création de compte. Le type générique <User> indique la forme de la réponse.
export const register = (body: RegisterInput) => request<User>('/auth/register', { method: 'POST', body })
// Profil de l'utilisateur connecté. Pas de corps, donc GET par défaut.
export const fetchMe = () => request<User>('/auth/me')

// ---- Mon compte ------------------------------------------------------------
// PATCH : mise à jour partielle du profil (seuls les champs fournis changent).
export const updateMe = (body: ProfileInput) => request<User>('/users/me', { method: 'PATCH', body })
// Suppression du compte. La réponse est vide, d'où le type void.
export const deleteMe = () => request<void>('/users/me', { method: 'DELETE' })
// Démarre l'activation de la 2FA : renvoie le secret et le QR code.
export const setupTwoFactor = () => request<TwoFactorSetup>('/auth/2fa/setup', { method: 'POST' })
// Valide l'activation avec un code de l'application d'authentification.
// Le type de réponse n'est pas précisé : la valeur renvoyée n'est pas utilisée par l'appelant.
export const enableTwoFactor = (code: string) => request('/auth/2fa/enable', { method: 'POST', body: { code } })
// Désactive la 2FA, en exigeant un code valide pour éviter qu'un tiers la retire.
export const disableTwoFactor = (code: string) => request('/auth/2fa/disable', { method: 'POST', body: { code } })
// Envoie un code de vérification par e-mail ou SMS. Le template literal construit l'URL selon la méthode choisie.
export const sendVerificationCode = (method: 'email' | 'sms') =>
  request<VerificationSent>(`/auth/verify/send-${method}`, { method: 'POST' })
// Vérifie le code saisi par l'utilisateur.
export const checkVerificationCode = (code: string) =>
  request('/auth/verify/check-code', { method: 'POST', body: { code } })

// ---- Public ------------------------------------------------------------------
// Liste des camps publiés, accessible sans connexion.
export const fetchPublicCamps = () => request<PublicCamp[]>('/public/camps')
// Détail d'un camp via son slug (identifiant lisible dans l'URL), sans connexion.
export const fetchPublicCamp = (slug: string) => request<PublicCamp>(`/camps/${enc(slug)}/public`)
// Inscription d'un visiteur à un camp.
export const registerToCamp = (slug: string, body: RegistrationInput) =>
  request<Registration>(`/camps/${enc(slug)}/registrations`, { method: 'POST', body })
// Envoi d'un message via le formulaire de contact du camp.
export const sendContactMessage = (slug: string, body: ContactInput) =>
  request<ContactMessage>(`/camps/${enc(slug)}/contact-messages`, { method: 'POST', body })
// Message au chatbot. sessionId est null au premier message ; le serveur en crée un et le renvoie.
// L'objet body n'inclut session_id que s'il existe, pour ne pas envoyer une valeur vide.
export const sendChatMessage = (slug: string, message: string, sessionId: string | null) =>
  request<ChatReply>(`/camps/${enc(slug)}/chat`, {
    method: 'POST',
    body: sessionId ? { message, session_id: sessionId } : { message },
  })

// ---- Organisateur ------------------------------------------------------------
// Données agrégées du tableau de bord.
export const fetchDashboard = () => request<DashboardSummary>('/dashboard/summary')
// Liste des camps de l'organisateur (vue interne, avec les champs privés).
export const fetchCamps = () => request<Camp[]>('/camps')
// Détail d'un camp par identifiant (et non par slug, contrairement à la partie publique).
export const fetchCamp = (id: string) => request<Camp>(`/camps/${enc(id)}`)
// Création d'un camp.
export const createCamp = (body: CampInput) => request<Camp>('/camps', { method: 'POST', body })
// Modification partielle. Partial<CampInput> : tous les champs sont facultatifs.
export const updateCamp = (id: string, body: Partial<CampInput>) =>
  request<Camp>(`/camps/${enc(id)}`, { method: 'PATCH', body })
// Suppression d'un camp.
export const deleteCamp = (id: string) => request<void>(`/camps/${enc(id)}`, { method: 'DELETE' })

// Enregistre ou publie la page d'accueil. PUT : remplace la ressource entière, à la différence de PATCH.
export const saveLandingPage = (campId: string, body: LandingPageInput) =>
  request(`/camps/${enc(campId)}/landing-page`, { method: 'PUT', body })

// Liste des inscriptions d'un camp.
export const fetchRegistrations = (campId: string) =>
  request<Registration[]>(`/camps/${enc(campId)}/registrations`)
// Marque la présence ou l'absence confirmée d'un inscrit.
export const setAttendance = (registrationId: string, confirmed: boolean) =>
  request<Registration>(`/registrations/${enc(registrationId)}/attendance`, {
    method: 'PATCH',
    body: { confirmed },
  })

// Messages de contact reçus pour un camp.
export const fetchMessages = (campId: string) =>
  request<ContactMessage[]>(`/camps/${enc(campId)}/contact-messages`)
// Change l'état d'un message (non lu, lu, archivé).
export const setMessageStatus = (messageId: string, status: MessageStatus) =>
  request<ContactMessage>(`/contact-messages/${enc(messageId)}`, { method: 'PATCH', body: { status } })

// Statistiques du chatbot pour un camp.
export const fetchChatStats = (campId: string) => request<ChatStats>(`/camps/${enc(campId)}/chat/stats`)
// Dernières conversations. limit=20 est écrit en dur dans l'URL : pas de pagination côté interface.
export const fetchConversations = (campId: string) =>
  request<Conversation[]>(`/camps/${enc(campId)}/chat/conversations?limit=20`)

// ---- Super admin -------------------------------------------------------------
// Liste complète des comptes utilisateurs.
export const fetchUsers = () => request<User[]>('/users')
// Création d'un compte par le super admin, avec un rôle défini.
export const createUser = (body: UserInput) => request<User>('/users', { method: 'POST', body })
// Change le rôle d'un utilisateur.
export const setUserRole = (id: string, role: UserRole) =>
  request<User>(`/users/${enc(id)}/role`, { method: 'PATCH', body: { role } })
// Change le statut d'un compte (actif, inactif, désactivé).
export const setUserStatus = (id: string, status: UserStatus) =>
  request<User>(`/users/${enc(id)}/status`, { method: 'PATCH', body: { status } })
// Suppression d'un compte utilisateur par le super admin.
export const deleteUser = (id: string) => request<void>(`/users/${enc(id)}`, { method: 'DELETE' })
// Liste des sauvegardes existantes.
export const fetchBackups = () => request<Backup[]>('/backups')
// Lance une nouvelle sauvegarde au format SQL ou CSV.
export const createBackup = (format: BackupFormat) => request<Backup>('/backups', { method: 'POST', body: { format } })
// Télécharge le fichier de sauvegarde sous forme de blob (donnée binaire), et non de JSON.
export const downloadBackup = (id: string) => requestBlob(`/backups/${enc(id)}/download`)