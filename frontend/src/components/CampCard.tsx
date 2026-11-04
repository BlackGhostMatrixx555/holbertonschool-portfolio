// Link : lien de navigation interne de React Router (évite de recharger la page).
import { Link } from 'react-router-dom'
// Type des données d'un camp publié, tel que renvoyé par l'API.
import type { PublicCamp } from '../api/types'
// Fonctions de mise en forme des dates et de l'âge.
import { formatAge, formatRange } from '../lib/format'
// Déduction de la saison et styles Tailwind associés à chaque saison.
import { seasonFromDate, seasonStyles } from '../lib/season'

/** Carte d'un camp sur la page d'accueil. Toute la carte est cliquable. */
export function CampCard({ camp }: { camp: PublicCamp }) {
  // Saison choisie par l'organisateur si elle existe, sinon déduite de la date de début.
  // « ?? » ne se déclenche que si la valeur est null ou undefined.
  const season = camp.landing_page?.season_theme ?? seasonFromDate(camp.start_date)
  const style = seasonStyles[season]
  // Camp complet quand il ne reste aucune place.
  const full = camp.remaining_places === 0

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-navy-100 transition hover:-translate-y-0.5 hover:shadow-md">
      {/* Bandeau coloré de la saison. aria-hidden : purement décoratif, inutile pour les lecteurs d'écran. */}
      <div className={`h-2 ${style.accent}`} aria-hidden="true" />
      <div className="flex flex-1 flex-col p-5">
        <p className="text-sm font-medium text-navy-500">
          {/* L'émoji est décoratif, masqué aux lecteurs d'écran. */}
          <span aria-hidden="true">{style.emoji} </span>
          {/* Si la ville n'est pas renseignée, on affiche un texte de repli. */}
          {camp.city || 'Lieu à venir'}
        </p>
        <h3 className="mt-1 text-xl font-bold">
          {/* Le lien couvre toute la carte (::after) tout en restant un seul lien pour le clavier */}
          {/* after:absolute after:inset-0 : un pseudo-élément qui recouvre le parent « relative » (l'article). */}
          <Link to={`/camps/${camp.slug}`} className="after:absolute after:inset-0">
            {camp.name}
          </Link>
        </h3>
        {/* Description affichée seulement si elle existe ; line-clamp-2 la limite à deux lignes. */}
        {camp.description && <p className="mt-2 line-clamp-2 text-sm text-navy-700">{camp.description}</p>}
        {/* dl : liste de paires terme/définition, adaptée à des libellés et leurs valeurs. */}
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-navy-500">Dates</dt>
            <dd className="font-medium">{formatRange(camp.start_date, camp.end_date)}</dd>
          </div>
          <div>
            <dt className="text-navy-500">Âge</dt>
            <dd className="font-medium">{formatAge(camp.age)}</dd>
          </div>
        </dl>
        {/* Disponibilité : rouge si complet, vert sinon. */}
        <p className={`mt-4 text-sm font-semibold ${full ? 'text-coral-700' : 'text-spring'}`}>
          {/* Accord du pluriel : « 1 place restante », « 3 places restantes ». */}
          {full ? 'Complet' : `${camp.remaining_places} place${camp.remaining_places > 1 ? 's' : ''} restante${camp.remaining_places > 1 ? 's' : ''}`}
        </p>
      </div>
    </article>
  )
}