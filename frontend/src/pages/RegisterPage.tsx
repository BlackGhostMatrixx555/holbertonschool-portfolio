/**
 * Demande d'accès organisateur (inscription publique, apport de tete-work).
 * Le compte est créé inactif : le super admin doit le valider avant la première connexion.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { register as registerAccount } from '../api/endpoints'
import { Logo } from '../components/Logo'
import { Alert, Button, Field, inputClass } from '../components/ui'

const schema = z
  .object({
    first_name: z.string().trim().min(1, 'Le prénom est obligatoire.').max(100),
    last_name: z.string().trim().min(1, 'Le nom est obligatoire.').max(100),
    email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),
    phone_number: z
      .string()
      .trim()
      .regex(/^(\+?[0-9 .-]{6,20})?$/, 'Numéro de téléphone invalide.'),
    // 12 caractères minimum, comme l'API (recommandation ANSSI).
    password: z.string().min(12, '12 caractères minimum.').max(128),
    confirm: z.string(),
  })
  .refine((data) => data.password === data.confirm, {
    path: ['confirm'],
    message: 'Les deux mots de passe ne correspondent pas.',
  })

type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { phone_number: '' } })

  const mutation = useMutation({
    // La confirmation ne sert qu'au contrôle côté navigateur : elle n'est pas envoyée.
    mutationFn: (values: FormValues) =>
      registerAccount({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        phone_number: values.phone_number || undefined,
      }),
  })

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-900 px-4 py-12">
      <main className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-xl sm:p-8">
        <Logo />
        <h1 className="mt-6 text-2xl font-bold">Demander un accès organisateur</h1>

        {mutation.isSuccess ? (
          <div className="mt-6 space-y-4">
            <Alert tone="success">
              <p className="font-semibold">Demande envoyée !</p>
              <p>Votre compte sera actif dès sa validation par l'administrateur de la plateforme.</p>
            </Alert>
            <Link to="/connexion" className="inline-block font-semibold text-coral-600 hover:underline">
              Retour à la connexion
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-1 text-sm text-navy-500">
              Votre compte sera validé par l'administrateur avant votre première connexion.
            </p>
            <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="mt-6 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Prénom" required error={errors.first_name?.message}>
                  {(props) => <input {...props} {...register('first_name')} autoComplete="given-name" className={inputClass} />}
                </Field>
                <Field label="Nom" required error={errors.last_name?.message}>
                  {(props) => <input {...props} {...register('last_name')} autoComplete="family-name" className={inputClass} />}
                </Field>
              </div>
              <Field label="Email professionnel" required error={errors.email?.message}>
                {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
              </Field>
              <Field label="Téléphone" error={errors.phone_number?.message} hint="Facultatif : permet la vérification par SMS.">
                {(props) => <input {...props} {...register('phone_number')} type="tel" autoComplete="tel" className={inputClass} />}
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Mot de passe" required error={errors.password?.message} hint="12 caractères minimum.">
                  {(props) => (
                    <input {...props} {...register('password')} type="password" autoComplete="new-password" className={inputClass} />
                  )}
                </Field>
                <Field label="Confirmation" required error={errors.confirm?.message}>
                  {(props) => (
                    <input {...props} {...register('confirm')} type="password" autoComplete="new-password" className={inputClass} />
                  )}
                </Field>
              </div>
              {mutation.error && <Alert>{mutation.error.message}</Alert>}
              <Button type="submit" disabled={mutation.isPending} className="w-full">
                {mutation.isPending ? 'Envoi…' : 'Envoyer ma demande'}
              </Button>
            </form>
            <p className="mt-6 text-center text-sm text-navy-500">
              Déjà un compte ?{' '}
              <Link to="/connexion" className="font-semibold text-coral-600 hover:underline">
                Se connecter
              </Link>
            </p>
          </>
        )}
      </main>
    </div>
  )
}
