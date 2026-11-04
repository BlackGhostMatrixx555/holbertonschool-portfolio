/**
 * Sauvegardes (super admin) : créer un export SQL ou CSV, consulter
 * l'historique et retélécharger un export (historique repris de tete-work).
 */

// useMutation : écriture avec suivi d'état. useQuery : lecture avec cache.
// useQueryClient : accès au cache pour l'invalider après une création.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// Fonctions d'appel à l'API pour les sauvegardes.
import { createBackup, downloadBackup, fetchBackups } from '../../api/endpoints'

// Type BackupFormat : 'sql' ou 'csv'.
import type { BackupFormat } from '../../api/types'

// Composants d'interface partagés.
import { Alert, Button, Card, EmptyState, PageHeader, Spinner } from '../../components/ui'

// Formatage des dates.
import { formatDateTime } from '../../lib/format'

/**
 * Déclenche le téléchargement d'un fichier reçu de l'API.
 * Crée une URL temporaire pointant vers le fichier, simule un clic sur un lien,
 * puis libère l'URL.
 */
function saveFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob) // URL temporaire en mémoire
  const link = document.createElement('a')
  link.href = url
  link.download = filename // nom proposé à l'enregistrement
  link.click() // déclenche le téléchargement
  URL.revokeObjectURL(url) // libère la mémoire
}

export function BackupsPage() {
  const queryClient = useQueryClient()

  // Historique des sauvegardes. staleTime: 0 : la liste est considérée périmée
  // dès son chargement, donc rechargée à chaque affichage de la page.
  const history = useQuery({ queryKey: ['backups'], queryFn: fetchBackups, staleTime: 0 })

  // Création d'une sauvegarde. Après succès, l'historique est rechargé.
  const create = useMutation({
    mutationFn: (format: BackupFormat) => createBackup(format),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['backups'] }),
  })

  // Téléchargement d'une sauvegarde existante. La réponse contient le fichier (blob) et son nom.
  const download = useMutation({
    mutationFn: downloadBackup,
    onSuccess: ({ blob, filename }) => saveFile(blob, filename),
  })

  // Une seule erreur affichée : celle de la création, sinon celle du téléchargement.
  const error = create.error ?? download.error

  return (
    <>
      <PageHeader
        title="Sauvegardes"
        subtitle="Exportez la base de données PostgreSQL et retrouvez les exports précédents."
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="text-lg font-bold">Export SQL</h2>
          <p className="mt-2 text-sm text-navy-500">
            Dump complet produit par pg_dump : permet de restaurer toute la base sur un autre serveur.
          </p>
          {/* Désactivé pendant toute création, quel que soit le format choisi. */}
          <Button className="mt-4" disabled={create.isPending} onClick={() => create.mutate('sql')}>
            Créer un export .sql
          </Button>
        </Card>

        <Card>
          <h2 className="text-lg font-bold">Export CSV</h2>
          <p className="mt-2 text-sm text-navy-500">
            Une archive .zip avec un fichier CSV par table, lisible dans un tableur.
          </p>
          <Button className="mt-4" variant="secondary" disabled={create.isPending} onClick={() => create.mutate('csv')}>
            Créer un export .zip
          </Button>
        </Card>
      </div>

      <div className="mt-6 space-y-3">
        {create.isPending && <Alert tone="info">Préparation de la sauvegarde…</Alert>}
        {create.isSuccess && <Alert tone="success">Sauvegarde créée : elle apparaît dans l'historique.</Alert>}
        {error && <Alert>{error.message}</Alert>}
      </div>

      <Card className="mt-6">
        <h2 className="text-lg font-bold">Historique</h2>
        <div className="mt-4">
          {history.isPending && <Spinner />}
          {history.isError && <Alert>{history.error.message}</Alert>}
          {history.data?.length === 0 && <EmptyState title="Aucune sauvegarde pour l'instant" />}

          {history.data && history.data.length > 0 && (
            <ul className="divide-y divide-navy-100">
              {history.data.map((backup) => (
                <li key={backup.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-sm">
                    <p className="font-semibold uppercase">{backup.format === 'sql' ? 'SQL' : 'CSV (.zip)'}</p>
                    {/* « ? » si la taille n'est pas connue. */}
                    <p className="text-navy-500">
                      {formatDateTime(backup.created_at)} · {backup.file_size_kb ?? '?'} Ko
                    </p>
                  </div>
                  <Button variant="secondary" disabled={download.isPending} onClick={() => download.mutate(backup.id)}>
                    Télécharger<span className="sr-only"> la sauvegarde du {formatDateTime(backup.created_at)}</span>
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>

      <div className="mt-6">
        <Alert tone="info">
          Ces fichiers contiennent des données personnelles (emails, inscriptions de mineurs). Conservez-les dans un
          espace sécurisé et supprimez-les quand ils ne sont plus utiles.
        </Alert>
      </div>
    </>
  )
}