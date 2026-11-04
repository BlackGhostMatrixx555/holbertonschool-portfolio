/**
 * Landing page publique d'un camp : compte à rebours saisonnier, infos pratiques,
 * inscription, partage LinkedIn, contact et chatbot.
 */

// useQuery : récupère les données du camp, avec cache et états de chargement/erreur.
import { useQuery } from '@tanstack/react-query'

// useEffect : exécute du code en réaction à un changement (ici, le titre de l'onglet).
import { useEffect } from 'react'

// useParams : lit les paramètres de l'URL, ici le "slug" du camp (ex. /camps/python-ete-2026).
import { useParams } from 'react-router-dom'

// ApiError : classe d'erreur renvoyée par le client HTTP, permet de lire le code de statut (404...).
import { ApiError } from '../api/client'

// Fonction d'appel à l'API pour récupérer un camp public à partir de son slug.
import { fetchPublicCamp } from '../api/endpoints'

// Composants propres à la page : chatbot, formulaire de contact, compte à rebours, formulaire d'inscription.
import { ChatWidget } from '../components/ChatWidget'
import { ContactForm } from '../components/ContactForm'
import { CountdownTimer } from '../components/CountdownTimer'
import { RegistrationForm } from '../components/RegistrationForm'

// Composants d'interface partagés.
import { Card, LinkButton, Spinner } from '../components/ui'

// Fonctions de mise en forme : dates, tranche d'âge, libellés des modalités.
import { formatAge, formatDay, modalityLabels } from '../lib/format'

// Gestion du thème saisonnier : déduction de la saison et styles associés (couleurs, emoji).
import { seasonFromDate, seasonStyles } from '../lib/season'

export function CampPage() {
  // Récupère le slug depuis l'URL. La valeur par défaut '' évite un undefined si le paramètre est absent.
  const { slug = '' } = useParams()

  // Requête du camp. La clé inclut le slug : chaque camp a son propre cache.
  // L'arrow function () => fetchPublicCamp(slug) permet de passer le slug à la fonction.
  const query = useQuery({ queryKey: ['public-camp', slug], queryFn: () => fetchPublicCamp(slug) })

  // Raccourci : données du camp, ou undefined tant que la requête n'a pas abouti.
  const camp = query.data

  // Mise à jour du titre de l'onglet avec le nom du camp, puis remise à zéro au démontage.
  useEffect(() => {
    if (camp) document.title = `${camp.name} – CampOrga`
    // Fonction de nettoyage : appelée quand on quitte la page ou quand camp change.
    return () => {
      document.title = 'CampOrga – Summer camps de code'
    }
  }, [camp])

  // Premier état : chargement en cours.
  if (query.isPending) return <Spinner label="Chargement du camp…" />

  // Deuxième état : erreur ou camp absent.
  if (query.isError || !camp) {
    // Distingue le cas « camp introuvable » (404) des autres erreurs pour afficher un message adapté.
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

  // Thème saisonnier : priorité au thème défini par l'organisateur, sinon déduit de la date de début.
  const season = camp.landing_page?.season_theme ?? seasonFromDate(camp.start_date)
  const style = seasonStyles[season]

  // URL de partage LinkedIn. encodeURIComponent protège l'adresse courante pour qu'elle soit valide dans un paramètre d'URL.
  const shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`

  return (
    <>
      {/* Bandeau d'accroche : titre, description, boutons d'action et compte à rebours. */}
      <section className={`${style.soft} border-b border-navy-100`}>
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_1fr] lg:items-center lg:py-16">
          <div>
            <p className={`text-sm font-semibold uppercase tracking-widest ${style.text}`}>
              {/* aria-hidden : l'emoji est décoratif, le lecteur d'écran lit seulement la ville. */}
              <span aria-hidden="true">{style.emoji} </span>
              {camp.city}
            </p>

            {/* Titre marketing si fourni, sinon nom du camp. || (et non ??) : une chaîne vide est aussi remplacée. */}
            <h1 className="mt-2 text-4xl font-bold leading-tight sm:text-5xl">{camp.landing_page?.hero_title || camp.name}</h1>

            {/* Le nom du camp n'apparaît en sous-titre que si un titre marketing le remplace. */}
            {camp.landing_page?.hero_title && <p className="mt-1 text-lg font-medium text-navy-700">{camp.name}</p>}

            {camp.landing_page?.hero_description && (
              <p className="mt-4 max-w-xl text-lg text-navy-700">{camp.landing_page.hero_description}</p>
            )}

            <div className="mt-6 flex flex-wrap gap-3">
              {/* Ancre vers le formulaire d'inscription, plus bas dans la page. */}
              <a href="#inscription" className="rounded-xl bg-coral-600 px-5 py-3 font-semibold text-white hover:bg-coral-700">
                Je m'inscris
              </a>

              {/* target="_blank" ouvre dans un nouvel onglet. rel="noopener noreferrer" empêche la page LinkedIn d'accéder à window.opener et ne transmet pas le referrer. */}
              <a
                href={shareUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl bg-white px-5 py-3 font-semibold text-navy-900 ring-1 ring-navy-100 hover:bg-navy-50"
              >
                Partager sur LinkedIn
                {/* sr-only : texte visible uniquement pour les lecteurs d'écran, qui annoncent l'ouverture d'une nouvelle fenêtre. */}
                <span className="sr-only"> (nouvelle fenêtre)</span>
              </a>
            </div>
          </div>

          {/* Compte à rebours vers la date de début. */}
          <div className="rounded-3xl bg-white/70 p-5 shadow-sm ring-1 ring-navy-100 sm:p-6">
            <CountdownTimer startDate={camp.start_date} season={season} />
          </div>
        </div>
      </section>

      {/* Contenu principal : colonne gauche informations, colonne droite inscription et contact. */}
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-bold">Infos pratiques</h2>

            {/* dl/dt/dd : liste de paires terme/définition, adaptée aux données clé-valeur. */}
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

              {/* col-span-2 : la ligne des places occupe toute la largeur. */}
              <div className="col-span-2">
                <dt className="text-navy-500">Places restantes</dt>
                {/* Couleur rouge si complet, verte sinon. */}
                <dd className={`text-lg font-bold ${camp.remaining_places === 0 ? 'text-coral-700' : 'text-spring'}`}>
                  {camp.remaining_places === 0 ? 'Complet' : camp.remaining_places}
                </dd>
              </div>
            </dl>
          </Card>

          {/* Affichée seulement si une description existe. whitespace-pre-line conserve les retours à la ligne saisis. */}
          {camp.description && (
            <Card>
              <h2 className="text-xl font-bold">Au programme</h2>
              <p className="mt-3 whitespace-pre-line text-navy-700">{camp.description}</p>
            </Card>
          )}

          {/* Liste des modalités, seulement si elle n'est pas vide. */}
          {camp.modalities.length > 0 && (
            <Card>
              <h2 className="text-xl font-bold">Modalités</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {camp.modalities.map((modality, index) => (
                  // key={index} : acceptable ici car la liste est statique. Avec une liste modifiable, un identifiant stable est préférable.
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
          {/* Formulaire d'inscription. scroll-mt-20 et scroll-mt-24 compensent les éléments fixes lors du défilement vers l'ancre #inscription. */}
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

      {/* Chatbot flottant, rendu en dernier pour qu'il reste au-dessus du contenu. */}
      <ChatWidget slug={camp.slug} campName={camp.name} />
    </>
  )
}