import { Link } from 'react-router-dom'
import type { PublicCamp } from '../api/types'
import { formatAge, formatRange } from '../lib/format'
import { seasonFromDate, seasonStyles } from '../lib/season'

/** Carte d'un camp sur la page d'accueil. Toute la carte est cliquable. */
export function CampCard({ camp }: { camp: PublicCamp }) {
  const season = camp.landing_page?.season_theme ?? seasonFromDate(camp.start_date)
  const style = seasonStyles[season]
  const full = camp.remaining_places === 0

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-navy-100 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className={`h-2 ${style.accent}`} aria-hidden="true" />
      <div className="flex flex-1 flex-col p-5">
        <p className="text-sm font-medium text-navy-500">
          <span aria-hidden="true">{style.emoji} </span>
          {camp.city || 'Lieu à venir'}
        </p>
        <h3 className="mt-1 text-xl font-bold">
          {/* Le lien couvre toute la carte (::after) tout en restant un seul lien pour le clavier */}
          <Link to={`/camps/${camp.slug}`} className="after:absolute after:inset-0">
            {camp.name}
          </Link>
        </h3>
        {camp.description && <p className="mt-2 line-clamp-2 text-sm text-navy-700">{camp.description}</p>}
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
        <p className={`mt-4 text-sm font-semibold ${full ? 'text-coral-700' : 'text-spring'}`}>
          {full ? 'Complet' : `${camp.remaining_places} place${camp.remaining_places > 1 ? 's' : ''} restante${camp.remaining_places > 1 ? 's' : ''}`}
        </p>
      </div>
    </article>
  )
}
