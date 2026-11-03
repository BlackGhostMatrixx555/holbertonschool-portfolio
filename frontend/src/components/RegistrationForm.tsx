/**
 * Formulaire public d'inscription (cahier des charges, module 4.4) :
 * prénom, nom, email, commentaire optionnel et case de confirmation.
 *
 * La validation côté client (zod) donne un retour immédiat à l'utilisateur ;
 * l'API revalide tout de son côté, car le navigateur n'est jamais de confiance.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { ApiError } from '../api/client'
import { registerToCamp } from '../api/endpoints'
import { Alert, Button, Field, inputClass } from './ui'

const schema = z.object({
  first_name: z.string().trim().min(1, 'Le prénom est obligatoire.').max(100),
  last_name: z.string().trim().min(1, 'Le nom est obligatoire.').max(100),
  email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),
  comment: z.string().max(1000, '1000 caractères maximum.').optional(),
  confirm: z.literal(true, { error: 'Merci de confirmer votre participation.' }),
})

type FormValues = z.input<typeof schema>

export function RegistrationForm({ slug, remainingPlaces }: { slug: string; remainingPlaces: number }) {
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      registerToCamp(slug, {
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        email: values.email.trim(),
        comment: values.comment?.trim() || undefined,
      }),
    onSuccess: () => {
      reset()
      // Les places restantes ont changé : on recharge les données du camp.
      void queryClient.invalidateQueries({ queryKey: ['public-camp', slug] })
      void queryClient.invalidateQueries({ queryKey: ['public-camps'] })
    },
  })

  if (mutation.isSuccess) {
    return (
      <Alert tone="success">
        <p className="font-semibold">Inscription enregistrée !</p>
        <p>L'équipe organisatrice reviendra vers vous par email. À très vite au camp.</p>
      </Alert>
    )
  }

  if (remainingPlaces === 0) {
    return <Alert tone="info">Ce camp est complet. Contactez l'équipe pour être prévenu(e) d'une prochaine session.</Alert>
  }

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Prénom" required error={errors.first_name?.message}>
          {(props) => <input {...props} {...register('first_name')} autoComplete="given-name" className={inputClass} />}
        </Field>
        <Field label="Nom" required error={errors.last_name?.message}>
          {(props) => <input {...props} {...register('last_name')} autoComplete="family-name" className={inputClass} />}
        </Field>
      </div>
      <Field label="Email" required error={errors.email?.message} hint="Utilisé uniquement pour vous contacter au sujet du camp.">
        {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
      </Field>
      <Field label="Commentaire" error={errors.comment?.message} hint="Facultatif : régime alimentaire, question…">
        {(props) => <textarea {...props} {...register('comment')} rows={3} className={inputClass} />}
      </Field>

      <div>
        <label className="flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            {...register('confirm')}
            aria-invalid={Boolean(errors.confirm)}
            className="mt-0.5 h-5 w-5 rounded border-navy-100 accent-coral-600"
          />
          <span>Je confirme ma participation à ce camp.</span>
        </label>
        {errors.confirm && <p className="mt-1 text-xs font-medium text-coral-700">{errors.confirm.message}</p>}
      </div>

      {mutation.error && (
        <Alert>{mutation.error instanceof ApiError ? mutation.error.message : "L'inscription a échoué."}</Alert>
      )}

      <Button type="submit" disabled={mutation.isPending} className="w-full sm:w-auto">
        {mutation.isPending ? 'Envoi…' : "Je m'inscris"}
      </Button>
    </form>
  )
}
