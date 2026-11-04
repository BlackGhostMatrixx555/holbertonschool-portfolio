/**
 * Formulaire public d'inscription (cahier des charges, module 4.4) :
 * prénom, nom, email, commentaire optionnel et case de confirmation.
 *
 * La validation côté client (zod) donne un retour immédiat à l'utilisateur ;
 * l'API revalide tout de son côté, car le navigateur n'est jamais de confiance.
 */
// zodResolver : relie le schéma zod à react-hook-form pour qu'il valide les champs.
import { zodResolver } from '@hookform/resolvers/zod'
// useMutation : gère un envoi (POST) avec ses états (en cours, succès, erreur). useQueryClient : accès au cache des données.
import { useMutation, useQueryClient } from '@tanstack/react-query'
// useForm : gestion des champs, de leurs valeurs et des erreurs.
import { useForm } from 'react-hook-form'
import { z } from 'zod'
// ApiError : erreur renvoyée par l'API, avec un message exploitable.
import { ApiError } from '../api/client'
import { registerToCamp } from '../api/endpoints'
import { Alert, Button, Field, inputClass } from './ui'

// Schéma de validation : chaque règle produit un message en français.
const schema = z.object({
  // trim() retire les espaces superflus avant de vérifier la longueur. max(100) limite la taille.
  first_name: z.string().trim().min(1, 'Le prénom est obligatoire.').max(100),
  last_name: z.string().trim().min(1, 'Le nom est obligatoire.').max(100),
  // pipe enchaîne deux vérifications : présence, puis format d'adresse email.
  email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),
  // Champ facultatif : peut être absent.
  comment: z.string().max(1000, '1000 caractères maximum.').optional(),
  // Doit valoir exactement true (case cochée). Sinon, le message de confirmation s'affiche.
  confirm: z.literal(true, { error: 'Merci de confirmer votre participation.' }),
})

// Type des valeurs saisies, déduit du schéma. z.input : valeurs avant transformation.
type FormValues = z.input<typeof schema>

// slug : identifiant du camp dans l'URL de l'API. remainingPlaces : nombre de places encore libres.
export function RegistrationForm({ slug, remainingPlaces }: { slug: string; remainingPlaces: number }) {
  const queryClient = useQueryClient()
  const {
    register,        // relie un champ HTML au formulaire
    handleSubmit,    // exécute la validation puis la fonction fournie si tout est valide
    reset,           // vide le formulaire
    formState: { errors }, // erreurs de validation par champ
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    // Envoi à l'API : les espaces sont retirés, le commentaire vide devient undefined
    // pour ne pas être transmis.
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
      // void : on ignore volontairement la promesse retournée.
      void queryClient.invalidateQueries({ queryKey: ['public-camp', slug] })
      void queryClient.invalidateQueries({ queryKey: ['public-camps'] })
    },
  })

  // Après un envoi réussi, la confirmation remplace le formulaire.
  if (mutation.isSuccess) {
    return (
      <Alert tone="success">
        <p className="font-semibold">Inscription enregistrée !</p>
        <p>L'équipe organisatrice reviendra vers vous par email. À très vite au camp.</p>
      </Alert>
    )
  }

  // Plus de place : le formulaire n'est pas affiché.
  if (remainingPlaces === 0) {
    return <Alert tone="info">Ce camp est complet. Contactez l'équipe pour être prévenu(e) d'une prochaine session.</Alert>
  }

  return (
    // handleSubmit valide d'abord, puis lance mutation.mutate. noValidate désactive la validation native
    // du navigateur pour laisser place aux messages en français.
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Field : composant qui gère le libellé, l'erreur et les liens d'accessibilité. Les props sont transmises à l'input. */}
        <Field label="Prénom" required error={errors.first_name?.message}>
          {(props) => <input {...props} {...register('first_name')} autoComplete="given-name" className={inputClass} />}
        </Field>
        <Field label="Nom" required error={errors.last_name?.message}>
          {(props) => <input {...props} {...register('last_name')} autoComplete="family-name" className={inputClass} />}
        </Field>
      </div>
      <Field label="Email" required error={errors.email?.message} hint="Utilisé uniquement pour vous contacter au sujet du camp.">
        {/* type="email" : clavier adapté sur mobile. autoComplete aide le remplissage automatique. */}
        {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
      </Field>
      <Field label="Commentaire" error={errors.comment?.message} hint="Facultatif : régime alimentaire, question…">
        {(props) => <textarea {...props} {...register('comment')} rows={3} className={inputClass} />}
      </Field>

      <div>
        <label className="flex items-start gap-3 text-sm">
          {/* aria-invalid : signale l'erreur aux lecteurs d'écran. */}
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

      {/* Erreur d'envoi : message de l'API si connu, sinon message générique. */}
      {mutation.error && (
        <Alert>{mutation.error instanceof ApiError ? mutation.error.message : "L'inscription a échoué."}</Alert>
      )}

      {/* Désactivé pendant l'envoi pour éviter les doubles inscriptions. */}
      <Button type="submit" disabled={mutation.isPending} className="w-full sm:w-auto">
        {mutation.isPending ? 'Envoi…' : "Je m'inscris"}
      </Button>
    </form>
  )
}