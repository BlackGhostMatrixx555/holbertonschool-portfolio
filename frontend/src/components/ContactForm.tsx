/** Formulaire de contact (hotline) de la landing page. */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { sendContactMessage } from '../api/endpoints'
import { Alert, Button, Field, inputClass } from './ui'

const schema = z.object({
  name: z.string().trim().min(1, 'Votre nom est obligatoire.').max(100),
  email: z.string().trim().email('Adresse email invalide.'),
  message: z.string().trim().min(1, 'Le message est vide.').max(2000, '2000 caractères maximum.'),
})

type FormValues = z.infer<typeof schema>

export function ContactForm({ slug }: { slug: string }) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => sendContactMessage(slug, values),
    onSuccess: () => reset(),
  })

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nom" required error={errors.name?.message}>
          {(props) => <input {...props} {...register('name')} autoComplete="name" className={inputClass} />}
        </Field>
        <Field label="Email" required error={errors.email?.message}>
          {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
        </Field>
      </div>
      <Field label="Message" required error={errors.message?.message}>
        {(props) => <textarea {...props} {...register('message')} rows={4} className={inputClass} />}
      </Field>
      {mutation.isSuccess && <Alert tone="success">Message envoyé. Un organisateur vous répondra par email.</Alert>}
      {mutation.error && <Alert>{mutation.error.message}</Alert>}
      <Button type="submit" variant="secondary" disabled={mutation.isPending}>
        {mutation.isPending ? 'Envoi…' : 'Envoyer le message'}
      </Button>
    </form>
  )
}
