// screen : requêtes sur le rendu (trouver un élément comme le ferait un utilisateur).
import { screen } from '@testing-library/react'
// userEvent : simule des interactions réalistes (saisie, clic) plutôt que des événements bruts.
import userEvent from '@testing-library/user-event'
// afterEach : hook de nettoyage. describe / it / expect : structure et assertions. vi : utilitaires de mock.
import { afterEach, describe, expect, it, vi } from 'vitest'
// mockApi : simule les réponses de l'API. renderWithProviders : rend le composant avec les contextes nécessaires (routeur, requêtes).
import { mockApi, renderWithProviders } from '../test/utils'
import { RegistrationForm } from './RegistrationForm'

// Après chaque test, restaure les globales remplacées (ici fetch) pour éviter les effets de bord entre tests.
afterEach(() => vi.unstubAllGlobals())

describe('RegistrationForm', () => {
  it('affiche les erreurs sans appeler l’API si le formulaire est vide', async () => {
    // Aucune réponse attendue : l'appel réseau ne doit pas avoir lieu.
    const fetchMock = mockApi({})
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    // Les messages de validation apparaissent (attente asynchrone car la validation est déclenchée après le clic).
    expect(await screen.findByText('Le prénom est obligatoire.')).toBeInTheDocument()
    expect(screen.getByText('Merci de confirmer votre participation.')).toBeInTheDocument()
    // Le champ en erreur est signalé aux lecteurs d'écran
    expect(screen.getByLabelText(/Prénom/)).toHaveAttribute('aria-invalid', 'true')
    // Aucune requête envoyée : la validation côté client bloque bien l'envoi.
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('envoie l’inscription et affiche la confirmation', async () => {
    // Simule une création réussie (201) avec les données renvoyées par l'API.
    const fetchMock = mockApi({
      'POST /camps/camp-test/registrations': {
        status: 201,
        body: { id: 'r1', camp_id: 'c1', first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com', comment: null, confirmed: false },
      },
    })
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    // Remplit le formulaire et coche la case de confirmation, puis soumet.
    await userEvent.type(screen.getByLabelText(/Prénom/), 'Ada')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Lovelace')
    await userEvent.type(screen.getByLabelText(/Email/), 'ada@example.com')
    await userEvent.click(screen.getByLabelText('Je confirme ma participation à ce camp.'))
    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    // Confirmation affichée une fois la réponse reçue.
    expect(await screen.findByText('Inscription enregistrée !')).toBeInTheDocument()
    // Vérifie le corps envoyé : seuls les trois champs attendus doivent partir
    // (le commentaire et la case de confirmation ne sont pas transmis).
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(body).toEqual({ first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com' })
  })

  it('affiche le message de l’API en cas de doublon', async () => {
    // Simule un conflit (409) : l'email est déjà inscrit.
    mockApi({
      'POST /camps/camp-test/registrations': { status: 409, body: { detail: 'Une inscription existe déjà pour cet email.' } },
    })
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    await userEvent.type(screen.getByLabelText(/Prénom/), 'Ada')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Lovelace')
    await userEvent.type(screen.getByLabelText(/Email/), 'ada@example.com')
    await userEvent.click(screen.getByLabelText('Je confirme ma participation à ce camp.'))
    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    // Le message d'erreur renvoyé par l'API est affiché dans une alerte accessible.
    expect(await screen.findByRole('alert')).toHaveTextContent('Une inscription existe déjà pour cet email.')
  })

  it('n’affiche pas le formulaire quand le camp est complet', () => {
    mockApi({})
    // Aucune place restante : le formulaire doit être remplacé par un message.
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={0} />)
    expect(screen.getByText(/Ce camp est complet/)).toBeInTheDocument()
    // Le bouton d'envoi n'existe pas dans le DOM, donc impossible de s'inscrire.
    expect(screen.queryByRole('button', { name: "Je m'inscris" })).not.toBeInTheDocument()
  })
})