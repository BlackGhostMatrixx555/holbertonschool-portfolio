/**
 * Sauvegardes (super admin) : créer un export SQL ou CSV, consulter
 * l'historique et retélécharger un export (historique repris de tete-work).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createBackup, downloadBackup, fetchBackups } from '../../api/endpoints'
import type { BackupFormat } from '../../api/types'
import { Alert, Button, Card, EmptyState, PageHeader, Spinner } from '../../components/ui'
import { formatDateTime } from '../../lib/format'

/** Déclenche le téléchargement d'un fichier reçu de l'API. */
function saveFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url) // libère la mémoire
}

export function BackupsPage() {
  const queryClient = useQueryClient()
  const history = useQuery({ queryKey: ['backups'], queryFn: fetchBackups, staleTime: 0 })
  const create = useMutation({
    mutationFn: (format: BackupFormat) => createBackup(format),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['backups'] }),
  })
  const download = useMutation({
    mutationFn: downloadBackup,
    onSuccess: ({ blob, filename }) => saveFile(blob, filename),
  })
  const error = create.error ?? download.error

  return (
    <>
      <PageHeader title="Sauvegardes" subtitle="Exportez la base de données PostgreSQL et retrouvez les exports précédents." />
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="text-lg font-bold">Export SQL</h2>
          <p className="mt-2 text-sm text-navy-500">
            Dump complet produit par pg_dump : permet de restaurer toute la base sur un autre serveur.
          </p>
          <Button className="mt-4" disabled={create.isPending} onClick={() => create.mutate('sql')}>
            Créer un export .sql
          </Button>
        </Card>
        <Card>
          <h2 className="text-lg font-bold">Export CSV</h2>
          <p className="mt-2 text-sm text-navy-500">Une archive .zip avec un fichier CSV par table, lisible dans un tableur.</p>
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
