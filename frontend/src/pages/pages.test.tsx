import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { PublicCamp } from '../api/types'
import { RequireAuth } from '../auth/RequireAuth'
import { mockApi, renderWithProviders } from '../test/utils'
import { CampPage } from './CampPage'
import { HomePage } from './HomePage'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'

afterEach(() => vi.unstubAllGlobals())

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

describe('HomePage', () => {
  it('liste les camps publiés avec un lien vers leur page', async () => {
    mockApi({ 'GET /public/camps': { body: [camp] } })
    renderWithProviders(<HomePage />)
    const link = await screen.findByRole('link', { name: 'Code Explorers' })
    expect(link).toHaveAttribute('href', '/camps/code-explorers')
    expect(screen.getByText('3 places restantes')).toBeInTheDocument()
    expect(screen.getByText('À partir de 12 ans')).toBeInTheDocument()
  })

  it('affiche un état vide', async () => {
    mockApi({ 'GET /public/camps': { body: [] } })
    renderWithProviders(<HomePage />)
    expect(await screen.findByText('Aucun camp pour le moment')).toBeInTheDocument()
  })
})

describe('CampPage', () => {
  it('affiche la landing page du camp', async () => {
    mockApi({ 'GET /camps/code-explorers/public': { body: camp } })
    renderWithProviders(<CampPage />, { route: '/camps/code-explorers', path: '/camps/:slug' })
    expect(await screen.findByRole('heading', { level: 1, name: 'Code ton été' })).toBeInTheDocument()
    expect(screen.getByRole('timer')).toBeInTheDocument()
    expect(screen.getByText('Niveau collège')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Partager sur LinkedIn/ })).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('affiche « Camp introuvable » pour un camp non publié', async () => {
    mockApi({ 'GET /camps/brouillon/public': { status: 404, body: { detail: 'Camp introuvable.' } } })
    renderWithProviders(<CampPage />, { route: '/camps/brouillon', path: '/camps/:slug' })
    expect(await screen.findByRole('heading', { name: 'Camp introuvable' })).toBeInTheDocument()
  })
})

describe('Connexion et protection des pages', () => {
  it('redirige vers la connexion sans session', async () => {
    mockApi({})
    renderWithProviders(
      <RequireAuth>
        <p>Contenu privé</p>
      </RequireAuth>,
    )
    expect(await screen.findByText('Page de connexion')).toBeInTheDocument()
    expect(screen.queryByText('Contenu privé')).not.toBeInTheDocument()
  })

  it('affiche l’erreur de l’API quand les identifiants sont faux', async () => {
    mockApi({ 'POST /auth/login': { status: 401, body: { detail: 'Email ou mot de passe incorrect.' } } })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'mauvais-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou mot de passe incorrect.')
  })

  it('connecte l’utilisateur et l’envoie vers son espace', async () => {
    mockApi({
      'POST /auth/login': { body: { access_token: 'jwt', token_type: 'bearer', expires_in: 3600, requires_2fa: false, temp_token: null } },
      'GET /auth/me': { body: { id: 'u1', email: 'orga@example.com', first_name: 'Ada', last_name: null, phone_number: null, role: 'sem', status: 'active', is_2fa_enabled: false } },
    })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'bon-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))
    expect(await screen.findByText('Espace organisateur')).toBeInTheDocument()
    expect(sessionStorage.getItem('camporga.token')).toBe('jwt')
  })
})

describe('Double authentification et inscription', () => {
  it('demande le code à 6 chiffres quand la 2FA est activée', async () => {
    const fetchMock = mockApi({
      'POST /auth/login': { body: { access_token: null, token_type: 'bearer', expires_in: 0, requires_2fa: true, temp_token: 'temp' } },
      'POST /auth/2fa/login': { body: { access_token: 'jwt', token_type: 'bearer', expires_in: 3600, requires_2fa: false, temp_token: null } },
      'GET /auth/me': { body: { id: 'u1', email: 'orga@example.com', first_name: 'Ada', last_name: null, phone_number: null, role: 'sem', status: 'active', is_2fa_enabled: true } },
    })
    renderWithProviders(<LoginPage />, { route: '/connexion', path: '/connexion' })
    await userEvent.type(screen.getByLabelText(/Email/), 'orga@example.com')
    await userEvent.type(screen.getByLabelText(/Mot de passe/), 'bon-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))

    // Étape 2 : pas encore connecté, le code est demandé.
    expect(await screen.findByRole('heading', { name: 'Double authentification' })).toBeInTheDocument()
    expect(sessionStorage.getItem('camporga.token')).toBeNull()

    await userEvent.type(screen.getByLabelText(/Code de vérification/), '123456')
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }))
    expect(await screen.findByText('Espace organisateur')).toBeInTheDocument()
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
    await userEvent.type(await screen.findByLabelText(/Code de vérification/), '12ab')
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }))
    expect(await screen.findByText('Le code contient 6 chiffres.')).toBeInTheDocument()
  })

  it("envoie la demande d'accès et explique la validation", async () => {
    const fetchMock = mockApi({ 'POST /auth/register': { status: 201, body: { id: 'u2' } } })
    renderWithProviders(<RegisterPage />, { route: '/inscription', path: '/inscription' })
    await userEvent.type(screen.getByLabelText(/Prénom/), 'Grace')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Hopper')
    await userEvent.type(screen.getByLabelText(/Email professionnel/), 'grace@example.com')
    await userEvent.type(screen.getByLabelText(/^Mot de passe/), 'un-mot-de-passe-solide')
    await userEvent.type(screen.getByLabelText(/Confirmation/), 'un-mot-de-passe-solide')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer ma demande' }))

    expect(await screen.findByText('Demande envoyée !')).toBeInTheDocument()
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(body).toEqual({ first_name: 'Grace', last_name: 'Hopper', email: 'grace@example.com', password: 'un-mot-de-passe-solide' })
  })

  it('vérifie que les deux mots de passe correspondent', async () => {
    const fetchMock = mockApi({})
    renderWithProviders(<RegisterPage />, { route: '/inscription', path: '/inscription' })
    await userEvent.type(screen.getByLabelText(/^Mot de passe/), 'un-mot-de-passe-solide')
    await userEvent.type(screen.getByLabelText(/Confirmation/), 'un-autre-mot-de-passe')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer ma demande' }))
    expect(await screen.findByText('Les deux mots de passe ne correspondent pas.')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
