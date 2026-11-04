/**
 * Connexion des organisateurs et du super admin, en une ou deux étapes :
 * 1. email + mot de passe ;
 * 2. si la double authentification est activée : code à 6 chiffres de l'application.
 */

// Pont entre Zod et React Hook Form : le schéma Zod sert de règle de validation du formulaire.
import { zodResolver } from '@hookform/resolvers/zod'

// useState : état local de la page (erreur serveur, jeton temporaire de 2FA).
import { useState } from 'react'

// useForm : gère les champs, la validation et l'état de soumission.
import { useForm } from 'react-hook-form'

// Link : lien interne. Navigate : redirection déclarative. useLocation : lit l'URL et l'état de navigation. useNavigate : redirection impérative.
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

// z : bibliothèque de validation de schémas (Zod).
import { z } from 'zod'

// Hook du contexte d'authentification : accès à l'utilisateur courant, à login et à completeTwoFactor.
import { useAuth } from '../auth/useAuth'

// Logo et composants d'interface partagés.
import { Logo } from '../components/Logo'
import { Alert, Button, Field, inputClass } from '../components/ui'

// Schéma de l'étape 1 : email et mot de passe. Le mot de passe est seulement requis ici, la règle de longueur n'est vérifiée qu'à l'inscription.
const credentialsSchema = z.object({
  email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),
  password: z.string().min(1, 'Le mot de passe est obligatoire.'),
})

// Type TypeScript déduit du schéma : évite de le redéclarer à la main.
type Credentials = z.infer<typeof credentialsSchema>

// Schéma de l'étape 2 : exactement 6 chiffres, pour le code TOTP.
const codeSchema = z.object({
  code: z.string().regex(/^\d{6}$/, 'Le code contient 6 chiffres.'),
})
type CodeValues = z.infer<typeof codeSchema>

// Sous-composant pour l'étape 2 de la double authentification.
// Reçoit le jeton temporaire, puis deux callbacks : succès (onDone) et retour arrière (onCancel).
function TwoFactorStep({ tempToken, onDone, onCancel }: { tempToken: string; onDone: () => void; onCancel: () => void }) {
  const { completeTwoFactor } = useAuth()

  // Erreur renvoyée par le serveur (code faux, expiré...), distincte des erreurs de format détectées côté client.
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CodeValues>({ resolver: zodResolver(codeSchema) })

  // Soumission : on efface l'erreur précédente, on tente la validation du code, puis on signale le succès.
  async function onSubmit({ code }: CodeValues) {
    setServerError(null)
    try {
      await completeTwoFactor(tempToken, code)
      onDone()
    } catch (error) {
      // Message de l'erreur s'il existe, sinon un texte générique.
      setServerError(error instanceof Error ? error.message : 'Code refusé.')
    }
  }

  return (
    // noValidate : désactive la validation native du navigateur, au profit de celle de Zod.
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
      <p className="text-sm text-navy-700">
        Ouvrez votre application d'authentification et saisissez le code à 6 chiffres affiché pour CampOrga.
      </p>
      <Field label="Code de vérification" required error={errors.code?.message}>
        {(props) => (
          <input
            {...props}
            {...register('code')}
            inputMode="numeric"            // clavier numérique sur mobile
            autoComplete="one-time-code"   // permet au navigateur ou au système de proposer le code automatiquement
            maxLength={6}
            autoFocus                      // le champ reçoit le focus dès l'affichage de l'étape
            className={`${inputClass} text-center font-mono text-2xl tracking-[0.5em]`}
          />
        )}
      </Field>
      {serverError && <Alert>{serverError}</Alert>}
      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? 'Vérification…' : 'Valider'}
      </Button>
      {/* Bouton secondaire pour revenir à l'étape 1 sans recharger la page. */}
      <Button type="button" variant="ghost" className="w-full" onClick={onCancel}>
        Revenir à la connexion
      </Button>
    </form>
  )
}

// Page de connexion principale.
export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [serverError, setServerError] = useState<string | null>(null)

  // Jeton temporaire renvoyé après l'étape 1 lorsque la 2FA est requise. Sa présence change l'affichage.
  const [tempToken, setTempToken] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Credentials>({ resolver: zodResolver(credentialsSchema) })

  // Page à laquelle renvoyer après connexion. RequireAuth la transmet dans l'état de navigation.
  // Si elle est absente, on retourne à l'espace organisateur par défaut.
  const from = (location.state as { from?: string } | null)?.from ?? '/espace'

  // Si l'utilisateur est déjà connecté, on ne lui montre pas le formulaire.
  // Ce return est placé après tous les hooks : l'ordre des hooks doit rester constant entre les rendus.
  if (user) return <Navigate to={from} replace />

  // Étape 1 : envoi de l'email et du mot de passe.
  async function onSubmit(values: Credentials) {
    setServerError(null)
    try {
      const result = await login(values.email, values.password)
      // Si la 2FA est requise, on garde le jeton temporaire et on affiche l'étape 2.
      // Sinon, la connexion est complète : redirection immédiate.
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

        {/* Le titre change selon l'étape. */}
        <h1 className="mt-6 text-2xl font-bold">{tempToken ? 'Double authentification' : 'Espace organisateur'}</h1>

        {tempToken ? (
          <TwoFactorStep
            tempToken={tempToken}
            onDone={() => navigate(from, { replace: true })}
            onCancel={() => setTempToken(null)}   // réinitialiser le jeton revient à l'étape 1
          />
        ) : (
          <>
            <p className="mt-1 text-sm text-navy-500">Connectez-vous pour gérer vos camps.</p>
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
              <Field label="Email" required error={errors.email?.message}>
                {/* autoComplete="username" : aide les gestionnaires de mots de passe à reconnaître le champ identifiant. */}
                {(props) => <input {...props} {...register('email')} type="email" autoComplete="username" className={inputClass} />}
              </Field>
              <Field label="Mot de passe" required error={errors.password?.message}>
                {/* autoComplete="current-password" : indique qu'il s'agit d'un mot de passe existant, pas d'un nouveau. */}
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