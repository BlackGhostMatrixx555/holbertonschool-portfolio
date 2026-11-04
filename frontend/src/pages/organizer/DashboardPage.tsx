/** Tableau de bord organisateur : indicateurs, liste des camps, dernières inscriptions. */

// useQuery : récupère des données avec cache, chargement et gestion d'erreur.
import { useQuery } from '@tanstack/react-query'

// Link : lien interne vers une autre route, sans rechargement de la page.
import { Link } from 'react-router-dom'

// Fonctions d'appel à l'API : résumé du tableau de bord et liste des camps de l'organisateur.
import { fetchCamps, fetchDashboard } from '../../api/endpoints'

// Hook du contexte d'authentification, utilisé ici pour récupérer le prénom de l'utilisateur.
import { useAuth } from '../../auth/useAuth'

// Composants d'interface partagés : mise en page, alerte, badge de statut, etc.
import { Alert, Card, EmptyState, LinkButton, PageHeader, Spinner, StatusBadge } from '../../components/ui'

// Fonctions de mise en forme des dates.
import { formatDateTime, formatRange } from '../../lib/format'

// Petit composant local : une carte d'indicateur (libellé + valeur).
// Typé en ligne : label et value sont obligatoires, value est un nombre.
function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-navy-100">
      <p className="text-sm text-navy-500">{label}</p>
      <p className="mt-1 font-display text-3xl font-bold">{value}</p>
    </div>
  )
}

export function DashboardPage() {
  // Utilisateur connecté, pour personnaliser le message d'accueil.
  const { user } = useAuth()

  // Résumé : compteurs et inscriptions récentes.
  // staleTime: 0 indique que les données sont considérées comme périmées dès leur réception, donc elles sont rechargées
  // à chaque montage ou retour sur la page. Choix pertinent pour un tableau de bord qui doit être à jour.
  const summary = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard, staleTime: 0 })

  // Liste des camps de l'organisateur, avec la même logique de rechargement.
  const camps = useQuery({ queryKey: ['camps'], queryFn: fetchCamps, staleTime: 0 })

  // Table de correspondance id -> nom de camp, pour afficher le nom d'un camp à partir de son id dans les inscriptions.
  // camps.data?.map(...) renvoie undefined tant que les données ne sont pas là. new Map(undefined) crée une Map vide, sans erreur.
  const campNames = new Map(camps.data?.map((camp) => [camp.id, camp.name]))

  return (
    <>
      {/* En-tête : titre personnalisé, sous-titre, bouton d'action. */}
      <PageHeader
        // Ajoute le prénom seulement s'il existe. Le ternaire évite d'afficher « Bonjour undefined ».
        title={`Bonjour${user?.first_name ? ` ${user.first_name}` : ''} 👋`}
        subtitle="Vue d'ensemble de vos camps et des inscriptions récentes."
        actions={<LinkButton to="/espace/camps/nouveau">Créer un camp</LinkButton>}
      />

      {/* Erreur sur le résumé : affichée au-dessus des indicateurs. */}
      {summary.isError && <Alert>{summary.error.message}</Alert>}

      {/* Indicateurs : affichés seulement si les données sont disponibles. */}
      {/* aria-label donne un nom à la région pour les lecteurs d'écran (sans titre visible). */}
      {summary.data && (
        <section aria-label="Indicateurs" className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Camps" value={summary.data.camps.total} />
          <Stat label="Publiés" value={summary.data.camps.published} />
          <Stat label="Brouillons" value={summary.data.camps.draft} />
          <Stat label="Inscriptions" value={summary.data.registrations.total} />
        </section>
      )}

      {/* Grille principale : liste des camps à gauche (plus large), inscriptions à droite, sur les grands écrans. */}
      <div className="mt-8 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <h2 className="text-lg font-bold">Mes camps</h2>
          <div className="mt-4">
            {/* Chargement : spinner sans libellé. */}
            {camps.isPending && <Spinner />}

            {camps.isError && <Alert>{camps.error.message}</Alert>}

            {/* État vide : invitation à créer un premier camp, avec un lien. */}
            {camps.data?.length === 0 && (
              <EmptyState title="Aucun camp pour l'instant">
                <Link to="/espace/camps/nouveau" className="font-semibold text-coral-600 hover:underline">
                  Créez votre premier camp
                </Link>
              </EmptyState>
            )}

            {/* Liste des camps. */}
            {camps.data && camps.data.length > 0 && (
              // divide-y : séparateurs horizontaux entre les lignes.
              <ul className="divide-y divide-navy-100">
                {camps.data.map((camp) => (
                  // flex-col sur mobile, flex-row à partir de sm : la mise en page s'adapte à la largeur.
                  <li key={camp.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      {/* min-w-0 permet à un texte long de se réduire et de ne pas déborder dans un flex. */}
                      <Link to={`/espace/camps/${camp.id}`} className="font-semibold hover:text-coral-600">
                        {camp.name}
                      </Link>
                      <p className="text-sm text-navy-500">
                        {camp.city || 'Lieu à définir'} · {formatRange(camp.start_date, camp.end_date)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      {/* tabular-nums : chiffres de largeur fixe, pour que les compteurs ne bougent pas quand ils changent. */}
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

          {/* Message si la liste est vide. Ne s'affiche que si summary.data existe (évite un faux message pendant le chargement). */}
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
                  {/* Nom du camp via la Map. Repli sur « Camp » si le nom n'est pas encore chargé ou introuvable. */}
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