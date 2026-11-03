/**
 * Connexion des organisateurs et du super admin, en une ou deux étapes :
 * 1. email + mot de passe ;
 * 2. si la double authentification est activée : code à 6 chiffres de l'application.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../auth/useAuth'
import { Logo } from '../components/Logo'
import { Alert, Button, Field, inputClass } from '../components/ui'

const credentialsSchema = z.object({
  email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),
  password: z.string().min(1, 'Le mot de passe est obligatoire.'),
})
type Credentials = z.infer<typeof credentialsSchema>

const codeSchema = z.object({
  code: z.string().regex(/^\d{6}$/, 'Le code contient 6 chiffres.'),
})
type CodeValues = z.infer<typeof codeSchema>

function TwoFactorStep({ tempToken, onDone, onCancel }: { tempToken: string; onDone: () => void; onCancel: () => void }) {
  const { completeTwoFactor } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CodeValues>({ resolver: zodResolver(codeSchema) })

  async function onSubmit({ code }: CodeValues) {
    setServerError(null)
    try {
      await completeTwoFactor(tempToken, code)
      onDone()
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Code refusé.')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
      <p className="text-sm text-navy-700">
        Ouvrez votre application d'authentification et saisissez le code à 6 chiffres affiché pour CampOrga.
      </p>
      <Field label="Code de vérification" required error={errors.code?.message}>
        {(props) => (
          <input
            {...props}
            {...register('code')}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            autoFocus
            className={`${inputClass} text-center font-mono text-2xl tracking-[0.5em]`}
          />
        )}
      </Field>
      {serverError && <Alert>{serverError}</Alert>}
      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? 'Vérification…' : 'Valider'}
      </Button>
      <Button type="button" variant="ghost" className="w-full" onClick={onCancel}>
        Revenir à la connexion
      </Button>
    </form>
  )
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = useState<string | null>(null)
  const [tempToken, setTempToken] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Credentials>({ resolver: zodResolver(credentialsSchema) })

  // Page demandée avant la redirection vers la connexion (voir RequireAuth).
  const from = (location.state as { from?: string } | null)?.from ?? '/espace'

  if (user) return <Navigate to={from} replace />

  async function onSubmit(values: Credentials) {
    setServerError(null)
    try {
      const result = await login(values.email, values.password)
      if (result.status === 'two-factor') setTempToken(result.tempToken)
      else navigate(from, { replace: true })
    } catch (error) {
      setServerError(error instanceof Error ? error.message : 'Connexion impossible.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-900 px-4 py-12">
      <main className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl sm:p-8">
        <Logo />
        <h1 className="mt-6 text-2xl font-bold">{tempToken ? 'Double authentification' : 'Espace organisateur'}</h1>
        {tempToken ? (
          <TwoFactorStep
            tempToken={tempToken}
            onDone={() => navigate(from, { replace: true })}
            onCancel={() => setTempToken(null)}
          />
        ) : (
          <>
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
            <p className="mt-6 text-center text-sm text-navy-500">
              Pas encore de compte ?{' '}
              <Link to="/inscription" className="font-semibold text-coral-600 hover:underline">
                Demander un accès organisateur
              </Link>
            </p>
          </>
        )}
      </main>
    </div>
  )
}
