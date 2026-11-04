/** Gestion des comptes par le super admin : création, rôle, statut. */

// zodResolver : relie un schéma Zod à react-hook-form.
import { zodResolver } from '@hookform/resolvers/zod'

// useMutation : écriture avec suivi d'état. useQuery : lecture avec cache.
// useQueryClient : accès au cache pour l'invalider après une modification.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// useForm : gestion du formulaire de création.
import { useForm } from 'react-hook-form'

// z : bibliothèque de validation de schémas.
import { z } from 'zod'

// Fonctions d'appel à l'API pour les comptes.
import { createUser, deleteUser, fetchUsers, setUserRole, setUserStatus } from '../../api/endpoints'

// Types : UserRole (rôle), UserStatus (statut).
import type { UserRole, UserStatus } from '../../api/types'

// useAuth : permet de reconnaître l'utilisateur connecté (pour le désactiver dans la liste).
import { useAuth } from '../../auth/useAuth'

// Composants d'interface partagés.
import { Alert, Button, Card, Field, inputClass, PageHeader, Spinner } from '../../components/ui'

// Libellés traduits pour les rôles et les statuts.
import { roleLabels, userStatusLabels } from '../../lib/format'

// Liste des rôles, dérivée des clés de roleLabels. Le cast indique à TypeScript que la liste n'est pas vide.
const roles = Object.keys(roleLabels) as UserRole[]

// Règles de création d'un compte.
const schema = z.object({
  first_name: z.string().trim().min(1, 'Prénom obligatoire.').max(100),
  last_name: z.string().trim().min(1, 'Nom obligatoire.').max(100),
  // Vérifie le format de l'email, après suppression des espaces.
  email: z.string().trim().pipe(z.email('Adresse email invalide.')),
  // 12 caractères minimum, comme l'API (recommandation ANSSI).
  password: z.string().min(12, '12 caractères minimum.').max(128),
  // Le rôle doit faire partie de la liste des rôles connus.
  role: z.enum(roles as [UserRole, ...UserRole[]]),
})
type FormValues = z.infer<typeof schema>

function CreateUserForm() {
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'sem' }, // rôle par défaut proposé à la création
  })

  const mutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      reset() // vide le formulaire après succès
      void queryClient.invalidateQueries({ queryKey: ['users'] }) // recharge la liste
    },
  })

  return (
    <Card>
      <h2 className="mb-4 text-lg font-bold">Créer un compte</h2>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Prénom" required error={errors.first_name?.message}>
            {(props) => <input {...props} {...register('first_name')} className={inputClass} />}
          </Field>
          <Field label="Nom" required error={errors.last_name?.message}>
            {(props) => <input {...props} {...register('last_name')} className={inputClass} />}
          </Field>
          <Field label="Email" required error={errors.email?.message}>
            {/* autoComplete="off" : évite que le navigateur propose les identifiants d'un autre compte. */}
            {(props) => <input {...props} {...register('email')} type="email" autoComplete="off" className={inputClass} />}
          </Field>
          <Field label="Mot de passe provisoire" required error={errors.password?.message} hint="12 caractères minimum.">
            {/* autoComplete="new-password" : indique au navigateur qu'il s'agit d'un nouveau mot de passe, pas d'un existant. */}
            {(props) => (
              <input {...props} {...register('password')} type="password" autoComplete="new-password" className={inputClass} />
            )}
          </Field>
          <Field label="Rôle" required>
            {(props) => (
              <select {...props} {...register('role')} className={inputClass}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {roleLabels[role]}
                  </option>
                ))}
              </select>
            )}
          </Field>
        </div>
        {mutation.isSuccess && <Alert tone="success">Compte créé.</Alert>}
        {mutation.error && <Alert>{mutation.error.message}</Alert>}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Création…' : 'Créer le compte'}
        </Button>
      </form>
    </Card>
  )
}

export function UsersPage() {
  // Utilisateur connecté, pour empêcher de modifier son propre compte depuis la liste.
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()

  const users = useQuery({ queryKey: ['users'], queryFn: fetchUsers })

  // Fonction commune de rechargement de la liste après chaque modification.
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] })

  // Trois mutations distinctes, chacune suivant son propre état (erreur, chargement).
  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: UserRole }) => setUserRole(id, role),
    onSuccess: invalidate,
  })
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: UserStatus }) => setUserStatus(id, status),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({ mutationFn: deleteUser, onSuccess: invalidate })

  // Une seule erreur affichée : la première rencontrée parmi les trois actions.
  const error = roleMutation.error ?? statusMutation.error ?? deleteMutation.error

  // Nombre de comptes inactifs : demandes d'accès publiques qui attendent une validation.
  const pending = users.data?.filter((user) => user.status === 'inactive').length ?? 0

  return (
    <>
      <PageHeader title="Utilisateurs" subtitle="Comptes des organisateurs et leurs droits." />
      <div className="space-y-6">
        {pending > 0 && (
          <Alert tone="info">
            {pending} demande(s) d'accès en attente : passez leur statut à « Actif » pour les valider.
          </Alert>
        )}

        <Card>
          {users.isPending && <Spinner />}
          {users.isError && <Alert>{users.error.message}</Alert>}
          {error && <Alert>{error.message}</Alert>}

          {users.data && (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[48rem] text-left text-sm">
                <caption className="sr-only">Comptes utilisateurs</caption>
                <thead className="border-b border-navy-100 text-navy-500">
                  <tr>
                    <th scope="col" className="py-2 pr-4 font-medium">Nom</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Email</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Rôle</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Statut</th>
                    <th scope="col" className="py-2 font-medium">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-100">
                  {users.data.map((user) => {
                    // Le super admin ne peut pas modifier son propre compte.
                    const isMe = user.id === currentUser?.id
                    // Nom affiché : prénom + nom, ou tiret si aucun nom n'est renseigné.
                    const name = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() || '–'

                    return (
                      // Ligne surlignée si le compte attend une validation.
                      <tr key={user.id} className={user.status === 'inactive' ? 'bg-summer-soft/60' : undefined}>
                        <td className="py-3 pr-4 font-medium">
                          {name} {isMe && <span className="text-xs text-navy-500">(vous)</span>}
                        </td>
                        <td className="py-3 pr-4">{user.email}</td>

                        <td className="py-3 pr-4">
                          {/* aria-label : nom accessible du select, car il n'a pas de label visible. */}
                          <select
                            aria-label={`Rôle de ${name}`}
                            value={user.role}
                            disabled={isMe}
                            onChange={(event) => roleMutation.mutate({ id: user.id, role: event.target.value as UserRole })}
                            className="rounded-lg border border-navy-100 bg-white px-2 py-1"
                          >
                            {roles.map((role) => (
                              <option key={role} value={role}>
                                {roleLabels[role]}
                              </option>
                            ))}
                          </select>
                        </td>

                        <td className="py-3 pr-4">
                          <select
                            aria-label={`Statut de ${name}`}
                            value={user.status}
                            disabled={isMe}
                            onChange={(event) =>
                              statusMutation.mutate({ id: user.id, status: event.target.value as UserStatus })
                            }
                            className="rounded-lg border border-navy-100 bg-white px-2 py-1"
                          >
                            {Object.entries(userStatusLabels).map(([value, label]) => (
                              <option key={value} value={value}>
                                {label}
                              </option>
                            ))}
                          </select>
                        </td>

                        <td className="py-3 text-right">
                          {/* Pas de suppression de soi-même, ni du super admin. */}
                          {!isMe && user.role !== 'super_admin' && (
                            <Button
                              variant="ghost"
                              disabled={deleteMutation.isPending}
                              onClick={() => {
                                if (window.confirm(`Supprimer le compte de ${name} ?`)) deleteMutation.mutate(user.id)
                              }}
                            >
                              Supprimer<span className="sr-only"> le compte de {name}</span>
                            </Button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <CreateUserForm />
      </div>
    </>
  )
}