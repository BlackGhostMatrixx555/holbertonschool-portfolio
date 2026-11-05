/**
 * Mon compte : profil, vérification email / SMS, double authentification
 * et suppression du compte (fonctionnalités reprises de tete-work).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import {
  checkVerificationCode,
  deleteMe,
  disableTwoFactor,
  enableTwoFactor,
  sendVerificationCode,
  setupTwoFactor,
  updateMe,
} from '../../api/endpoints'
import type { TwoFactorSetup, User } from '../../api/types'
import { isSuperAdmin, useAuth } from '../../auth/useAuth'
import { Alert, Button, Card, Field, inputClass, PageHeader } from '../../components/ui'
import { roleLabels } from '../../lib/format'

const codeSchema = z.object({ code: z.string().regex(/^\d{6}$/, 'Le code contient 6 chiffres.') })
type CodeValues = z.infer<typeof codeSchema>

/** Petit formulaire réutilisé pour saisir un code à 6 chiffres. */
function CodeForm({ label, submitLabel, onSubmit, pending }: {
  label: string
  submitLabel: string
  onSubmit: (code: string) => void
  pending: boolean
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CodeValues>({ resolver: zodResolver(codeSchema) })
  return (
    <form
      onSubmit={handleSubmit(({ code }) => {
        onSubmit(code)
        reset()
      })}
      noValidate
      className="flex flex-col gap-3 sm:flex-row sm:items-end"
    >
      <div className="sm:w-48">
        <Field label={label} error={errors.code?.message}>
          {(props) => (
            <input
              {...props}
              {...register('code')}
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              className={`${inputClass} font-mono tracking-widest`}
            />
          )}
        </Field>
      </div>
      <Button type="submit" disabled={pending}>
        {submitLabel}
      </Button>
    </form>
  )
}

// ---- Profil ----------------------------------------------------------------------

const profileSchema = z.object({
  first_name: z.string().trim().min(1, 'Le prénom est obligatoire.').max(100),
  last_name: z.string().trim().min(1, 'Le nom est obligatoire.').max(100),
  phone_number: z.string().trim().regex(/^(\+?[0-9 .-]{6,20})?$/, 'Numéro de téléphone invalide.'),
})
type ProfileValues = z.infer<typeof profileSchema>

function ProfileCard({ user }: { user: User }) {
  const { refreshUser } = useAuth()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { first_name: user.first_name ?? '', last_name: user.last_name ?? '', phone_number: user.phone_number ?? '' },
  })
  const mutation = useMutation({
    mutationFn: (values: ProfileValues) => updateMe({ ...values, phone_number: values.phone_number || null }),
    onSuccess: () => refreshUser(),
  })

  return (
    <Card>
      <h2 className="text-lg font-bold">Profil</h2>
      <p className="mt-1 text-sm text-navy-500">
        {user.email} · {roleLabels[user.role]}
      </p>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="mt-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Prénom" required error={errors.first_name?.message}>
            {(props) => <input {...props} {...register('first_name')} className={inputClass} />}
          </Field>
          <Field label="Nom" required error={errors.last_name?.message}>
            {(props) => <input {...props} {...register('last_name')} className={inputClass} />}
          </Field>
          <Field label="Téléphone" error={errors.phone_number?.message}>
            {(props) => <input {...props} {...register('phone_number')} type="tel" className={inputClass} />}
          </Field>
        </div>
        {mutation.isSuccess && <Alert tone="success">Profil enregistré.</Alert>}
        {mutation.error && <Alert>{mutation.error.message}</Alert>}
        <Button type="submit" variant="secondary" disabled={mutation.isPending}>
          Enregistrer
        </Button>
      </form>
    </Card>
  )
}

// ---- Vérification email / SMS -----------------------------------------------------

function VerificationCard({ user }: { user: User }) {
  const send = useMutation({ mutationFn: sendVerificationCode })
  const check = useMutation({ mutationFn: checkVerificationCode })

  return (
    <Card>
      <h2 className="text-lg font-bold">Vérifier mes coordonnées</h2>
      <p className="mt-1 text-sm text-navy-500">Recevez un code à usage unique, valable 5 minutes.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Button variant="secondary" disabled={send.isPending} onClick={() => send.mutate('email')}>
          Recevoir un code par email
        </Button>
        <Button variant="secondary" disabled={send.isPending || !user.phone_number} onClick={() => send.mutate('sms')}>
          Recevoir un code par SMS
        </Button>
      </div>
      {!user.phone_number && <p className="mt-2 text-xs text-navy-500">Ajoutez un téléphone dans votre profil pour le SMS.</p>}
      <div className="mt-4 space-y-3">
        {send.data && (
          <Alert tone="info">
            {send.data.message}
            {/* Envoi simulé : le code n'est affiché qu'en développement. */}
            {send.data.debug_code && <> (mode développement : <strong>{send.data.debug_code}</strong>)</>}
          </Alert>
        )}
        {send.error && <Alert>{send.error.message}</Alert>}
        {send.data && <CodeForm label="Code reçu" submitLabel="Vérifier" pending={check.isPending} onSubmit={(code) => check.mutate(code)} />}
        {check.isSuccess && <Alert tone="success">Coordonnées vérifiées.</Alert>}
        {check.error && <Alert>{check.error.message}</Alert>}
      </div>
    </Card>
  )
}

// ---- Double authentification ------------------------------------------------------

function TwoFactorCard({ user }: { user: User }) {
  const { refreshUser } = useAuth()
  // Activation en 2 temps : 1) l'API génère le secret et le QR code (setup),
  // 2) l'utilisateur scanne et confirme avec un premier code (enable).
  const [setup, setSetup] = useState<TwoFactorSetup | null>(null)
  const start = useMutation({ mutationFn: setupTwoFactor, onSuccess: setSetup })
  const enable = useMutation({
    mutationFn: enableTwoFactor,
    onSuccess: async () => {
      setSetup(null)
      await refreshUser()
    },
  })
  // La désactivation demande aussi un code valide (vérifié par l'API).
  const disable = useMutation({ mutationFn: disableTwoFactor, onSuccess: () => refreshUser() })
  const error = start.error ?? enable.error ?? disable.error

  return (
    <Card>
      <h2 className="text-lg font-bold">Double authentification</h2>
      <p className="mt-1 text-sm text-navy-500">
        En plus du mot de passe, un code à 6 chiffres de votre téléphone (Google Authenticator, Authy…) est demandé à
        chaque connexion.
      </p>

      <div className="mt-4 space-y-4">
        {user.is_2fa_enabled ? (
          <>
            <Alert tone="success">La double authentification est activée sur votre compte.</Alert>
            <p className="text-sm text-navy-700">Pour la désactiver, saisissez un code actuel de votre application.</p>
            <CodeForm label="Code actuel" submitLabel="Désactiver" pending={disable.isPending} onSubmit={(code) => disable.mutate(code)} />
          </>
        ) : setup ? (
          <>
            <ol className="list-decimal space-y-1 pl-5 text-sm text-navy-700">
              <li>Scannez ce QR code avec votre application d'authentification.</li>
              <li>Saisissez le code à 6 chiffres qu'elle affiche pour confirmer.</li>
            </ol>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <img src={setup.qr_code_base64} alt="QR code à scanner pour activer la double authentification" className="h-44 w-44 rounded-xl ring-1 ring-navy-100" />
              <p className="text-xs text-navy-500">
                Impossible de scanner ? Saisissez cette clé à la main :
                <code className="mt-1 block break-all rounded bg-sand-100 px-2 py-1 font-mono text-navy-900">{setup.secret}</code>
              </p>
            </div>
            <CodeForm label="Code affiché" submitLabel="Activer" pending={enable.isPending} onSubmit={(code) => enable.mutate(code)} />
          </>
        ) : (
          <Button onClick={() => start.mutate()} disabled={start.isPending}>
            Activer la double authentification
          </Button>
        )}
        {error && <Alert>{error.message}</Alert>}
      </div>
    </Card>
  )
}

// ---- Suppression du compte ------------------------------------------------------

function DeleteAccountCard() {
  const { logout } = useAuth()
  // Compte supprimé : on ferme la session. L'API refuse (409) tant que le compte gère des camps.
  const mutation = useMutation({ mutationFn: deleteMe, onSuccess: logout })
  return (
    <Card className="ring-coral-100">
      <h2 className="text-lg font-bold">Supprimer mon compte</h2>
      <p className="mt-1 text-sm text-navy-500">
        Suppression définitive. Elle est refusée tant que vous gérez des camps : supprimez-les ou demandez leur transfert
        d'abord.
      </p>
      {mutation.error && (
        <div className="mt-4">
          <Alert>{mutation.error.message}</Alert>
        </div>
      )}
      <Button
        variant="danger"
        className="mt-4"
        disabled={mutation.isPending}
        onClick={() => {
          if (window.confirm('Supprimer définitivement votre compte ?')) mutation.mutate()
        }}
      >
        Supprimer mon compte
      </Button>
    </Card>
  )
}

export function AccountPage() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <>
      <PageHeader title="Mon compte" subtitle="Vos informations et la sécurité de votre accès." />
      <div className="space-y-6">
        <ProfileCard user={user} />
        <TwoFactorCard user={user} />
        <VerificationCard user={user} />
        {/* Le compte super admin ne peut pas être supprimé (garde-fou côté API aussi). */}
        {!isSuperAdmin(user.role) && <DeleteAccountCard />}
      </div>
    </>
  )
}
