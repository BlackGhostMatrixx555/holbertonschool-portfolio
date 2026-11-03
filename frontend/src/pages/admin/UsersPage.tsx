/** Gestion des comptes par le super admin : création, rôle, statut. */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { createUser, deleteUser, fetchUsers, setUserRole, setUserStatus } from '../../api/endpoints'
import type { UserRole, UserStatus } from '../../api/types'
import { useAuth } from '../../auth/useAuth'
import { Alert, Button, Card, Field, inputClass, PageHeader, Spinner } from '../../components/ui'
import { roleLabels, userStatusLabels } from '../../lib/format'

const roles = Object.keys(roleLabels) as UserRole[]

const schema = z.object({
  first_name: z.string().trim().min(1, 'Prénom obligatoire.').max(100),
  last_name: z.string().trim().min(1, 'Nom obligatoire.').max(100),
  email: z.string().trim().pipe(z.email('Adresse email invalide.')),
  // 12 caractères minimum, comme l'API (recommandation ANSSI).
  password: z.string().min(12, '12 caractères minimum.').max(128),
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
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { role: 'sem' } })
  const mutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      reset()
      void queryClient.invalidateQueries({ queryKey: ['users'] })
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
            {(props) => <input {...props} {...register('email')} type="email" autoComplete="off" className={inputClass} />}
          </Field>
          <Field label="Mot de passe provisoire" required error={errors.password?.message} hint="12 caractères minimum.">
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
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const users = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] })
  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: UserRole }) => setUserRole(id, role),
    onSuccess: invalidate,
  })
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: UserStatus }) => setUserStatus(id, status),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({ mutationFn: deleteUser, onSuccess: invalidate })
  const error = roleMutation.error ?? statusMutation.error ?? deleteMutation.error
  // Comptes créés par l'inscription publique, en attente de validation.
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
                    const isMe = user.id === currentUser?.id
                    const name = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() || '–'
                    return (
                      <tr key={user.id} className={user.status === 'inactive' ? 'bg-summer-soft/60' : undefined}>
                        <td className="py-3 pr-4 font-medium">
                          {name} {isMe && <span className="text-xs text-navy-500">(vous)</span>}
                        </td>
                        <td className="py-3 pr-4">{user.email}</td>
                        <td className="py-3 pr-4">
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
