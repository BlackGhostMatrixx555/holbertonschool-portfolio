/** Page d'accueil : présentation et liste des camps publiés. */
import { useQuery } from '@tanstack/react-query'
import { fetchPublicCamps } from '../api/endpoints'
import { CampCard } from '../components/CampCard'
import { Alert, EmptyState, Spinner } from '../components/ui'

export function HomePage() {
  const camps = useQuery({ queryKey: ['public-camps'], queryFn: fetchPublicCamps })

  return (
    <>
      <section className="relative overflow-hidden bg-navy-900 text-white">
        {/* Décor géométrique purement visuel */}
        <div aria-hidden="true" className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-coral-600/30 blur-3xl" />
        <div aria-hidden="true" className="absolute -bottom-32 left-10 h-72 w-72 rounded-full bg-winter/30 blur-3xl" />
        <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <p className="text-sm font-semibold uppercase tracking-widest text-coral-400">Apprendre · Créer · Partager</p>
          <h1 className="mt-3 max-w-2xl text-4xl font-bold leading-tight sm:text-5xl">
            Des summer camps pour découvrir le code.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-navy-100">
            Programmation, web, robotique : choisissez votre camp et inscrivez-vous en moins d'une minute.
          </p>
          <a
            href="#camps"
            className="mt-8 inline-flex rounded-xl bg-coral-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-coral-700"
          >
            Voir les camps
          </a>
        </div>
      </section>

      <section id="camps" aria-labelledby="camps-title" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-12 sm:px-6">
        <h2 id="camps-title" className="text-2xl font-bold sm:text-3xl">
          Les prochains camps
        </h2>
        <div className="mt-6">
          {camps.isPending && <Spinner label="Chargement des camps…" />}
          {camps.isError && <Alert>{camps.error.message}</Alert>}
          {camps.data?.length === 0 && (
            <EmptyState title="Aucun camp pour le moment">Revenez bientôt, de nouvelles sessions arrivent.</EmptyState>
          )}
          {camps.data && camps.data.length > 0 && (
            <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {camps.data.map((camp) => (
                <li key={camp.id} className="flex">
                  <CampCard camp={camp} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  )
}
