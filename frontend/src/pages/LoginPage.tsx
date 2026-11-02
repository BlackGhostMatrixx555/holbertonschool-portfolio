/** Connexion des organisateurs et du super admin. */
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../auth/useAuth'
import { Logo } from '../components/Logo'
import { Alert, Button, Field, inputClass } from '../components/ui'

const schema = z.object({
  email: z.string().trim().min(1, "L'email est obligatoire.").email('Adresse email invalide.'),
  password: z.string().min(1, 'Le mot de passe est obligatoire.'),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  // Page demandée avant la redirection vers la connexion (voir RequireAuth).
  const from = (location.state as { from?: string } | null)?.from ?? '/espace'

  if (user) return <Navigate to={from} replace />

  async function onSubmit(values: FormValues) {
    setServerError(null)
    try {
      await login(values.email, values.password)
      navigate(from, { replace: true })
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Connexion impossible.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-900 px-4 py-12">
      <main className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl sm:p-8">
        <Logo />
        <h1 className="mt-6 text-2xl font-bold">Espace organisateur</h1>
        <p className="mt-1 text-sm text-navy-500">Connectez-vous pour gérer vos camps.</p>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
          <Field label="Email" required error={errors.email?.message}>
            {(props) => <input {...props} {...register('email')} type="email" autoComplete="username" className={inputClass} />}
          </Field>
          <Field label="Mot de passe" required error={errors.password?.message}>
            {(props) => (
              <input {...props} {...register('password')} type="password" autoComplete="current-password" className={inputClass} />
            )}
          </Field>
          {serverError && <Alert>{serverError}</Alert>}
          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? 'Connexion…' : 'Se connecter'}
          </Button>
        </form>
      </main>
    </div>
  )
}
