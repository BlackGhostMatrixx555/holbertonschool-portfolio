/** Tableau de bord organisateur : indicateurs, liste des camps, dernières inscriptions. */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchCamps, fetchDashboard } from '../../api/endpoints'
import { useAuth } from '../../auth/useAuth'
import { Alert, Card, EmptyState, LinkButton, PageHeader, Spinner, StatusBadge } from '../../components/ui'
import { formatDateTime, formatRange } from '../../lib/format'

/** Carte d'indicateur : un libellé et un grand nombre. */
function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-navy-100">
      <p className="text-sm text-navy-500">{label}</p>
      <p className="mt-1 font-display text-3xl font-bold">{value}</p>
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  // staleTime: 0 : les chiffres sont rechargés à chaque visite de la page.
  const summary = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard, staleTime: 0 })
  const camps = useQuery({ queryKey: ['camps'], queryFn: fetchCamps, staleTime: 0 })
  // Table id → nom, pour afficher le nom du camp à côté de chaque inscription récente.
  const campNames = new Map(camps.data?.map((camp) => [camp.id, camp.name]))

  return (
    <>
      <PageHeader
        title={`Bonjour${user?.first_name ? ` ${user.first_name}` : ''} 👋`}
        subtitle="Vue d'ensemble de vos camps et des inscriptions récentes."
        actions={<LinkButton to="/espace/camps/nouveau">Créer un camp</LinkButton>}
      />

      {summary.isError && <Alert>{summary.error.message}</Alert>}
      {summary.data && (
        <section aria-label="Indicateurs" className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Camps" value={summary.data.camps.total} />
          <Stat label="Publiés" value={summary.data.camps.published} />
          <Stat label="Brouillons" value={summary.data.camps.draft} />
          <Stat label="Inscriptions" value={summary.data.registrations.total} />
        </section>
      )}

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <h2 className="text-lg font-bold">Mes camps</h2>
          <div className="mt-4">
            {camps.isPending && <Spinner />}
            {camps.isError && <Alert>{camps.error.message}</Alert>}
            {camps.data?.length === 0 && (
              <EmptyState title="Aucun camp pour l'instant">
                <Link to="/espace/camps/nouveau" className="font-semibold text-coral-600 hover:underline">
                  Créez votre premier camp
                </Link>
              </EmptyState>
            )}
            {camps.data && camps.data.length > 0 && (
              <ul className="divide-y divide-navy-100">
                {camps.data.map((camp) => (
                  <li key={camp.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <Link to={`/espace/camps/${camp.id}`} className="font-semibold hover:text-coral-600">
                        {camp.name}
                      </Link>
                      <p className="text-sm text-navy-500">
                        {camp.city || 'Lieu à définir'} · {formatRange(camp.start_date, camp.end_date)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="tabular-nums text-navy-700">
                        {camp.registrations_count}/{camp.capacity} inscrits
                      </span>
                      <StatusBadge status={camp.status} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-bold">Dernières inscriptions</h2>
          {summary.data?.recent_registrations.length === 0 && (
            <p className="mt-4 text-sm text-navy-500">Pas encore d'inscription.</p>
          )}
          <ul className="mt-4 space-y-3">
            {summary.data?.recent_registrations.map((registration) => (
              <li key={registration.id} className="text-sm">
                <p className="font-medium">
                  {registration.first_name} {registration.last_name}
                </p>
                <p className="text-navy-500">
                  {campNames.get(registration.camp_id) ?? 'Camp'} · {formatDateTime(registration.created_at)}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  )
}
