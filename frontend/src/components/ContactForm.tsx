/** Formulaire de contact (hotline) de la landing page. */
// zodResolver : relie le schéma Zod à react-hook-form pour valider les champs.
import { zodResolver } from '@hookform/resolvers/zod'
// useMutation : gère l'envoi HTTP avec états (en cours, succès, erreur).
import { useMutation } from '@tanstack/react-query'
// useForm : gestion de formulaire (valeurs, erreurs, soumission).
import { useForm } from 'react-hook-form'
// z : bibliothèque de schémas de validation.
import { z } from 'zod'
// Fonction HTTP qui envoie le message au serveur.
import { sendContactMessage } from '../api/endpoints'
// Composants d'interface partagés.
import { Alert, Button, Field, inputClass } from './ui'

// Règles de validation de chaque champ.
const schema = z.object({
  // trim() retire les espaces avant contrôle ; min(1) refuse le champ vide ; max(100) borne la longueur.
  name: z.string().trim().min(1, 'Votre nom est obligatoire.').max(100),
  // pipe() enchaîne deux étapes : d'abord le texte nettoyé, puis la validation du format email.
  email: z.string().trim().pipe(z.email('Adresse email invalide.')),
  message: z.string().trim().min(1, 'Le message est vide.').max(2000, '2000 caractères maximum.'),
})

// Type TypeScript déduit du schéma : évite de le redéfinir à la main.
type FormValues = z.infer<typeof schema>

export function ContactForm({ slug }: { slug: string }) {
  const {
    // register relie un champ HTML au formulaire.
    register,
    // handleSubmit valide puis appelle la fonction fournie seulement si les données sont correctes.
    handleSubmit,
    // reset vide le formulaire.
    reset,
    // formState.errors contient les messages d'erreur de validation par champ.
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  // Mutation d'envoi. En cas de succès, le formulaire est vidé.
  const mutation = useMutation({
    mutationFn: (values: FormValues) => sendContactMessage(slug, values),
    onSuccess: () => reset(),
  })

  return (
    // noValidate : désactive la validation HTML native du navigateur, au profit de celle de Zod.
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Field : enveloppe avec libellé et message d'erreur. Le rendu prop reçoit des attributs
            comme id et aria-invalid, pour lier le libellé au champ. */}
        <Field label="Nom" required error={errors.name?.message}>
          {/* {...props} ajoute les attributs fournis par Field, {...register('name')} branche la saisie. */}
          {(props) => <input {...props} {...register('name')} autoComplete="name" className={inputClass} />}
        </Field>
        <Field label="Email" required error={errors.email?.message}>
          {/* type="email" : clavier adapté sur mobile ; autoComplete aide le remplissage automatique. */}
          {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
        </Field>
      </div>
      <Field label="Message" required error={errors.message?.message}>
        {(props) => <textarea {...props} {...register('message')} rows={4} className={inputClass} />}
      </Field>
      {/* Confirmation affichée après un envoi réussi. */}
      {mutation.isSuccess && <Alert tone="success">Message envoyé. Un organisateur vous répondra par email.</Alert>}
      {/* Message d'erreur renvoyé par l'API (ou par la requête). */}
      {mutation.error && <Alert>{mutation.error.message}</Alert>}
      {/* Bouton désactivé pendant l'envoi, pour éviter les doubles soumissions. */}
      <Button type="submit" variant="secondary" disabled={mutation.isPending}>
        {mutation.isPending ? 'Envoi…' : 'Envoyer le message'}
      </Button>
    </form>
  )
}