import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockApi, renderWithProviders } from '../test/utils'
import { RegistrationForm } from './RegistrationForm'

afterEach(() => vi.unstubAllGlobals())

describe('RegistrationForm', () => {
  it('affiche les erreurs sans appeler l’API si le formulaire est vide', async () => {
    const fetchMock = mockApi({})
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    expect(await screen.findByText('Le prénom est obligatoire.')).toBeInTheDocument()
    expect(screen.getByText('Merci de confirmer votre participation.')).toBeInTheDocument()
    // Le champ en erreur est signalé aux lecteurs d'écran
    expect(screen.getByLabelText(/Prénom/)).toHaveAttribute('aria-invalid', 'true')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('envoie l’inscription et affiche la confirmation', async () => {
    const fetchMock = mockApi({
      'POST /camps/camp-test/registrations': {
        status: 201,
        body: { id: 'r1', camp_id: 'c1', first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com', comment: null, confirmed: false },
      },
    })
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    await userEvent.type(screen.getByLabelText(/Prénom/), 'Ada')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Lovelace')
    await userEvent.type(screen.getByLabelText(/Email/), 'ada@example.com')
    await userEvent.click(screen.getByLabelText('Je confirme ma participation à ce camp.'))
    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    expect(await screen.findByText('Inscription enregistrée !')).toBeInTheDocument()
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(body).toEqual({ first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com' })
  })

  it('affiche le message de l’API en cas de doublon', async () => {
    mockApi({
      'POST /camps/camp-test/registrations': { status: 409, body: { detail: 'Une inscription existe déjà pour cet email.' } },
    })
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={5} />)

    await userEvent.type(screen.getByLabelText(/Prénom/), 'Ada')
    await userEvent.type(screen.getByLabelText(/^Nom/), 'Lovelace')
    await userEvent.type(screen.getByLabelText(/Email/), 'ada@example.com')
    await userEvent.click(screen.getByLabelText('Je confirme ma participation à ce camp.'))
    await userEvent.click(screen.getByRole('button', { name: "Je m'inscris" }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Une inscription existe déjà pour cet email.')
  })

  it('n’affiche pas le formulaire quand le camp est complet', () => {
    mockApi({})
    renderWithProviders(<RegistrationForm slug="camp-test" remainingPlaces={0} />)
    expect(screen.getByText(/Ce camp est complet/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: "Je m'inscris" })).not.toBeInTheDocument()
  })
})
