/**
 * Landing page publique d'un camp : compte à rebours saisonnier, infos pratiques,
 * inscription, partage LinkedIn, contact et chatbot.
 */
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { fetchPublicCamp } from '../api/endpoints'
import { ChatWidget } from '../components/ChatWidget'
import { ContactForm } from '../components/ContactForm'
import { CountdownTimer } from '../components/CountdownTimer'
import { RegistrationForm } from '../components/RegistrationForm'
import { Card, LinkButton, Spinner } from '../components/ui'
import { formatAge, formatDay, modalityLabels } from '../lib/format'
import { seasonFromDate, seasonStyles } from '../lib/season'

export function CampPage() {
  const { slug = '' } = useParams()
  const query = useQuery({ queryKey: ['public-camp', slug], queryFn: () => fetchPublicCamp(slug) })
  const camp = query.data

  // Titre de l'onglet : utile pour l'accessibilité et le référencement.
  useEffect(() => {
    if (camp) document.title = `${camp.name} – CampOrga`
    return () => {
      document.title = 'CampOrga – Summer camps de code'
    }
  }, [camp])

  if (query.isPending) return <Spinner label="Chargement du camp…" />
  if (query.isError || !camp) {
    const notFound = query.error instanceof ApiError && query.error.status === 404
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold">{notFound ? 'Camp introuvable' : 'Une erreur est survenue'}</h1>
        <p className="mt-2 text-navy-500">
          {notFound ? "Ce camp n'existe pas ou n'est plus publié." : query.error?.message}
        </p>
        <LinkButton to="/" variant="secondary" className="mt-6">
          Voir tous les camps
        </LinkButton>
      </div>
    )
  }

  const season = camp.landing_page?.season_theme ?? seasonFromDate(camp.start_date)
  const style = seasonStyles[season]
  const shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`

  return (
    <>
      <section className={`${style.soft} border-b border-navy-100`}>
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_1fr] lg:items-center lg:py-16">
          <div>
            <p className={`text-sm font-semibold uppercase tracking-widest ${style.text}`}>
              <span aria-hidden="true">{style.emoji} </span>
              {camp.city}
            </p>
            <h1 className="mt-2 text-4xl font-bold leading-tight sm:text-5xl">{camp.landing_page?.hero_title || camp.name}</h1>
            {camp.landing_page?.hero_title && <p className="mt-1 text-lg font-medium text-navy-700">{camp.name}</p>}
            {camp.landing_page?.hero_description && (
              <p className="mt-4 max-w-xl text-lg text-navy-700">{camp.landing_page.hero_description}</p>
            )}
            <div className="mt-6 flex flex-wrap gap-3">
              <a href="#inscription" className="rounded-xl bg-coral-600 px-5 py-3 font-semibold text-white hover:bg-coral-700">
                Je m'inscris
              </a>
              <a
                href={shareUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl bg-white px-5 py-3 font-semibold text-navy-900 ring-1 ring-navy-100 hover:bg-navy-50"
              >
                Partager sur LinkedIn<span className="sr-only"> (nouvelle fenêtre)</span>
              </a>
            </div>
          </div>
          <div className="rounded-3xl bg-white/70 p-5 shadow-sm ring-1 ring-navy-100 sm:p-6">
            <CountdownTimer startDate={camp.start_date} season={season} />
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-bold">Infos pratiques</h2>
            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-navy-500">Début</dt>
                <dd className="font-semibold">{formatDay(camp.start_date)}</dd>
              </div>
              <div>
                <dt className="text-navy-500">Fin</dt>
                <dd className="font-semibold">{formatDay(camp.end_date)}</dd>
              </div>
              <div>
                <dt className="text-navy-500">Lieu</dt>
                <dd className="font-semibold">{camp.city || 'À venir'}</dd>
              </div>
              <div>
                <dt className="text-navy-500">Âge</dt>
                <dd className="font-semibold">{formatAge(camp.age)}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-navy-500">Places restantes</dt>
                <dd className={`text-lg font-bold ${camp.remaining_places === 0 ? 'text-coral-700' : 'text-spring'}`}>
                  {camp.remaining_places === 0 ? 'Complet' : camp.remaining_places}
                </dd>
              </div>
            </dl>
          </Card>

          {camp.description && (
            <Card>
              <h2 className="text-xl font-bold">Au programme</h2>
              <p className="mt-3 whitespace-pre-line text-navy-700">{camp.description}</p>
            </Card>
          )}

          {camp.modalities.length > 0 && (
            <Card>
              <h2 className="text-xl font-bold">Modalités</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {camp.modalities.map((modality, index) => (
                  <li key={index} className="flex gap-2">
                    <span className="shrink-0 rounded-full bg-navy-50 px-2 py-0.5 text-xs font-semibold text-navy-700">
                      {modalityLabels[modality.type]}
                    </span>
                    <span>{modality.label}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card className="scroll-mt-20">
            <h2 id="inscription" className="scroll-mt-24 text-xl font-bold">
              Inscription
            </h2>
            <p className="mb-4 mt-1 text-sm text-navy-500">Trois informations et c'est fait. Les champs * sont obligatoires.</p>
            <RegistrationForm slug={camp.slug} remainingPlaces={camp.remaining_places} />
          </Card>

          <Card>
            <h2 className="text-xl font-bold">Une question ?</h2>
            <p className="mb-4 mt-1 text-sm text-navy-500">
              Écrivez à l'équipe, ou utilisez l'assistant en bas à droite pour une réponse immédiate.
            </p>
            <ContactForm slug={camp.slug} />
          </Card>
        </div>
      </div>

      <ChatWidget slug={camp.slug} campName={camp.name} />
    </>
  )
}

