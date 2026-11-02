/** Export des sauvegardes de la base (super admin). */
import { useMutation } from '@tanstack/react-query'
import { downloadBackup } from '../../api/endpoints'
import { Alert, Button, Card, PageHeader } from '../../components/ui'

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
  const mutation = useMutation({
    mutationFn: downloadBackup,
    onSuccess: ({ blob, filename }) => saveFile(blob, filename),
  })

  return (
    <>
      <PageHeader title="Sauvegardes" subtitle="Exportez la base de données PostgreSQL." />
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="text-lg font-bold">Export SQL</h2>
          <p className="mt-2 text-sm text-navy-500">
            Dump complet produit par pg_dump : permet de restaurer toute la base sur un autre serveur.
          </p>
          <Button className="mt-4" disabled={mutation.isPending} onClick={() => mutation.mutate('sql')}>
            Télécharger le .sql
          </Button>
        </Card>
        <Card>
          <h2 className="text-lg font-bold">Export CSV</h2>
          <p className="mt-2 text-sm text-navy-500">Une archive .zip avec un fichier CSV par table, lisible dans un tableur.</p>
          <Button className="mt-4" variant="secondary" disabled={mutation.isPending} onClick={() => mutation.mutate('csv')}>
            Télécharger le .zip
          </Button>
        </Card>
      </div>
      <div className="mt-6 space-y-3">
        {mutation.isPending && <Alert tone="info">Préparation de la sauvegarde…</Alert>}
        {mutation.error && <Alert>{mutation.error.message}</Alert>}
        <Alert tone="info">
          Ces fichiers contiennent des données personnelles (emails, inscriptions de mineurs). Conservez-les dans un
          espace sécurisé et supprimez-les quand ils ne sont plus utiles.
        </Alert>
      </div>
    </>
  )
}
