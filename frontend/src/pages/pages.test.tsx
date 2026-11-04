// screen : requêtes sur le DOM rendu, par rôle, libellé ou texte (ex. screen.getByRole).
import { screen } from '@testing-library/react'

// userEvent : simule des interactions utilisateur réalistes (taper, cliquer), plus fidèles que fireEvent.
import userEvent from '@testing-library/user-event'

// afterEach : nettoyage après chaque test. describe regroupe des tests, it définit un test, expect vérifie, vi crée des mocks.
import { afterEach, describe, expect, it, vi } from 'vitest'

// Type seul (effacé à la compilation) : forme d'un camp public, pour que les données de test soient typées.
import type { PublicCamp } from '../api/types'

// Garde de route : protège un contenu et redirige vers /connexion sans session.
import { RequireAuth } from '../auth/RequireAuth'

// Outils de test écrits précédemment : faux serveur (mockApi) et rendu avec les fournisseurs (renderWithProviders).
import { mockApi, renderWithProviders } from '../test/utils'

// Pages testées.
import { CampPage } from './CampPage'
import { HomePage } from './HomePage'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'

// Après chaque test, restaure les globaux modifiés (ici fetch remplacé par mockApi). Évite les fuites entre tests.
afterEach(() => vi.unstubAllGlobals())

// Donnée de test : un camp publié, conforme au type PublicCamp.
const camp: PublicCamp = {
  id: 'c1',
  name: 'Code Explorers',
  slug: 'code-explorers',
  description: 'Python, web et robotique.',
  start_date: '2027-07-06',
  end_date: '2027-07-17',
  city: 'Lyon',
  age: 12,
  status: 'published',
  remaining_places: 3,
  modalities: [{ type: 'education_level', label: 'Niveau collège' }],
  landing_page: { season_theme: 'summer', hero_title: 'Code ton été', hero_description: null, published_at: null },
}

// Groupe de tests pour la page d'accueil.
describe('HomePage', () => {
  it('liste les camps publiés avec un lien vers leur page', async () => {
    // Le faux serveur répond à GET /public/camps avec un camp.
    mockApi({ 'GET /public/camps': { body: [camp] } })
    renderWithProviders(<HomePage />)

    // findByRole attend que l'élément apparaisse (les données arrivent de façon asynchrone).
    const link = await screen.findByRole('link', { name: 'Code Explorers' })
    expect(link).toHaveAttribute('href', '/camps/code-explorers')

    // getByText est synchrone : l'élément doit déjà être affiché à ce stade.
    expect(screen.getByText('3 places restantes')).toBeInTheDocument()
    expect(screen.getByText('À partir de 12 ans')).toBeInTheDocument()
  })

  it('affiche un état vide', async () => {
    mockApi({ 'GET /public/camps': { body: [] } })
    renderWithProviders(<HomePage />)
    expect(await screen.findByText('Aucun camp pour le moment')).toBeInTheDocument()
  })
})

// Groupe de tests pour la landing page d'un camp.
describe('CampPage', () => {
  it('affiche la landing page du camp', async () => {
    mockApi({ 'GET /camps/code-explorers/public': { body: camp } })

    // route : l'URL simulée. path : le motif de route, pour que useParams récupère le slug.
    renderWithProviders(<CampPage />, { route: '/camps/code-explorers', path: '/camps/:slug' })

    // Le titre principal vient du titre de la landing page, pas du nom du camp.
    expect(await screen.findByRole('heading', { level: 1, name: 'Code ton été' })).toBeInTheDocument()

    // role="timer" : un compte à rebours est affiché (sans doute avant la date limite d'inscription).
    expect(screen.getByRole('timer')).toBeInTheDocument()
    expect(screen.getByText('Niveau collège')).toBeInTheDocument()

    // Le lien de partage doit ouvrir un nouvel onglet en sécurité (noopener noreferrer évite l'accès à window.opener).
    expect(screen.getByRole('link', { name: /Partager sur LinkedIn/ })).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('affiche « Camp introuvable » pour un camp non publié', async () => {
    // L'API répond 404 : la page doit gérer l'erreur sans planter.
    mockApi({ 'GET /camps/brouillon/public': { status: 404, body: { detail: 'Camp introuvable.' } } })
    renderWithProviders(<CampPage />, { route: '/camps/brouillon', path: '/camps/:slug' })
    expect(await screen.findByRole('heading', { name: 'Camp introuvable' })).toBeInTheDocument()
  })
})

// Groupe de tests pour la connexion et la protection des pages.
describe('Connexion et protection des pages', () => {
  it('redirige vers la connexion sans session', async () => {
    // Aucune route n'est nécessaire : sans session, aucun appel réseau n'est censé partir.
    mockApi({})
    renderWithProviders(
      <RequireAuth>
        <p>Contenu privé</p>
      </RequireAuth>,
    )

    // La redirection doit afficher la page de connexion simulée de renderWithProviders.
    expect(await screen.findByText('Page de connexion')).toBeInTheDocument()

    // Le contenu protégé ne doit jamais apparaître.
    expect(screen.queryByText('Contenu privé')).not.toBeInTheDocument()
  })

  it('affiche l’erreur de l’API quand les identifiants sont faux', async () => {
    mockApi({ 'POST /auth/login': { status: 401, body: { detail: 'Email ou mot de passe incorrect.' } } })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })

    // getByLabelText retrouve un champ par son libellé. La regex /Email/ tolère le texte autour.
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'mauvais-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))

    // role="alert" : l'erreur doit être annoncée aux lecteurs d'écran.
    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou mot de passe incorrect.')
  })

  it('connecte l’utilisateur et l’envoie vers son espace', async () => {
    mockApi({
      // Connexion réussie sans 2FA : le jeton arrive directement.
      'POST /auth/login': { body: { access_token: 'jwt', token_type: 'bearer', expires_in: 3600, requires_2fa: false, temp_token: null } },
      // Profil récupéré après connexion pour alimenter le contexte utilisateur.
      'GET /auth/me': { body: { id: 'u1', email: 'orga@example.com', first_name: 'Ada', last_name: null, phone_number: null, role: 'sem', status: 'active', is_2fa_enabled: false } },
    })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'bon-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))

    // La redirection vers /espace est simulée par renderWithProviders.
    expect(await screen.findByText('Espace organisateur')).toBeInTheDocument()

    // Le jeton est conservé en sessionStorage (il est vidé par le fichier de setup après chaque test).
    expect(sessionStorage.getItem('camporga.token')).toBe('jwt')
  })
})

// Groupe de tests pour la double authentification et l'inscription.
describe('Double authentification et inscription', () => {
  it('demande le code à 6 chiffres quand la 2FA est activée', async () => {
    // fetchMock est conservé pour vérifier ensuite le contenu des requêtes envoyées.
    const fetchMock = mockApi({
      // Première étape : identifiants valides, mais un code est requis. Un temp_token est renvoyé.
      'POST /auth/login': { body: { access_token: null, token_type: 'bearer', expires_in: 0, requires_2fa: true, temp_token: 'temp' } },
      // Deuxième étape : le code est vérifié et le vrai jeton arrive.
      'POST /auth/2fa/login': { body: { access_token: 'jwt', token_type: 'bearer', expires_in: 3600, requires_2fa: false, temp_token: null } },
      'GET /auth/me': { body: { id: 'u1', email: 'orga@example.com', first_name: 'Ada', last_name: null, phone_number: null, role: 'sem', status: 'active', is_2fa_enabled: true } },
    })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'bon-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))

    // Étape 2 : le formulaire de code remplace le formulaire de connexion.
    expect(await screen.findByRole('heading', { name: 'Double authentification' })).toBeInTheDocument()

    // Pas encore connecté : aucun jeton ne doit être stocké à ce stade.
    expect(sessionStorage.getItem('camporga.token')).toBeNull()

    await userEvent.type(screen.getByLabelText(/Code de vérification/), '123456')
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }))
    expect(await screen.findByText('Espace organisateur')).toBeInTheDocument()

    // calls[1] : deuxième appel réseau (le premier était /auth/login). On vérifie le corps envoyé.
    // Le "?." protège contre un body absent.
    const body = JSON.parse(String(fetchMock.mock.calls[1][1]?.body))
    expect(body).toEqual({ temp_token: 'temp', code: '123456' })
  })

  it('refuse un code qui ne fait pas 6 chiffres', async () => {
    mockApi({
      'POST /auth/login': { body: { access_token: null, token_type: 'bearer', expires_in: 0, requires_2fa: true, temp_token: 'temp' } },
    })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'bon-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))

    // Saisie invalide (lettres mélangées) : la validation côté client doit bloquer l'envoi.
    await userEvent.type(await screen.findByLabelText(/Code de vérification/), '12ab')
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }))
    expect(await screen.findByText('Le code contient 6 chiffres.')).toBeInTheDocument()
  })

  it("envoie la demande d'accès et explique la validation", async () => {
    // Le serveur répond 201 Created à la création du compte.
    const fetchMock = mockApi({ 'POST /auth/register': { status: 201, body: { id: 'u2' } } })
    renderWithProviders(<RegisterPage />, { route: '/inscription', path: '/inscription' })
    await userEvent.type(screen.getByLabelText(/Prénom/), 'Grace')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Hopper')
    await userEvent.type(screen.getByLabelText(/Email professionnel/), 'grace@example.com')

    // ^ dans la regex : libellé qui commence par "Mot de passe", pour ne pas confondre avec "Confirmation".
    await userEvent.type(screen.getByLabelText(/^Mot de passe/), 'un-mot-de-passe-solide')
    await userEvent.type(screen.getByLabelText(/Confirmation/), 'un-mot-de-passe-solide')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer ma demande' }))

    expect(await screen.findByText('Demande envoyée !')).toBeInTheDocument()

    // Vérifie le corps envoyé : la confirmation et le téléphone vide ne doivent pas apparaître.
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(body).toEqual({ first_name: 'Grace', last_name: 'Hopper', email: 'grace@example.com', password: 'un-mot-de-passe-solide' })
  })

  it('vérifie que les deux mots de passe correspondent', async () => {
    // Aucune route : si le formulaire est bien bloqué, aucun appel réseau ne doit partir.
    const fetchMock = mockApi({})
    renderWithProviders(<RegisterPage />, { route: '/inscription', path: '/inscription' })
    await userEvent.type(screen.getByLabelText(/^Mot de passe/), 'un-mot-de-passe-solide')
    await userEvent.type(screen.getByLabelText(/Confirmation/), 'un-autre-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer ma demande' }))
    expect(await screen.findByText('Les deux mots de passe ne correspondent pas.')).toBeInTheDocument()

    // Pas d'appel à l'API : la validation côté client a bien bloqué l'envoi.
    expect(fetchMock).not.toHaveBeenCalled()
  })
})