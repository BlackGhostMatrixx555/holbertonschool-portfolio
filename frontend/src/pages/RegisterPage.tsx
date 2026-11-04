/**
 * Demande d'accès organisateur (inscription publique, apport de tete-work).
 * Le compte est créé inactif : le super admin doit le valider avant la première connexion.
 * (Ce bloc JSDoc décrit le rôle de la page pour les autres développeurs.)
 */

// Pont entre Zod et React Hook Form : utilise le schéma Zod comme règle de validation du formulaire.
import { zodResolver } from '@hookform/resolvers/zod'

// useMutation : gère un appel qui modifie des données (ici, la création de compte), avec les états isPending, error, isSuccess.
import { useMutation } from '@tanstack/react-query'

// useForm : gère l'état, la validation et la soumission du formulaire.
import { useForm } from 'react-hook-form'

// Link : lien interne de React Router, sans rechargement de page.
import { Link } from 'react-router-dom'

// z : bibliothèque de validation de schémas (Zod).
import { z } from 'zod'

// Renommé en registerAccount pour éviter le conflit avec la fonction register de useForm.
import { register as registerAccount } from '../api/endpoints'

// Logo de la plateforme.
import { Logo } from '../components/Logo'

// Composants d'interface réutilisables : messages d'alerte, bouton, champ avec libellé et erreur, et classe CSS commune des inputs.
import { Alert, Button, Field, inputClass } from '../components/ui'

// Schéma de validation décrivant les règles de chaque champ du formulaire.
const schema = z
  .object({
    // trim() retire les espaces en début et fin, puis min(1) refuse un champ vide.
    first_name: z.string().trim().min(1, 'Le prénom est obligatoire.').max(100),
    last_name: z.string().trim().min(1, 'Le nom est obligatoire.').max(100),

    // pipe() enchaîne deux validations : d'abord la présence, puis le format d'email.
    // z.email() est la forme moderne de Zod v4 (z.string().email() est déprécié).
    email: z.string().trim().min(1, "L'email est obligatoire.").pipe(z.email('Adresse email invalide.')),

    // Facultatif : la regex accepte aussi une chaîne vide (le "?" devant le groupe).
    // Chiffres, espaces, points, tirets, et un + éventuel en tête, de 6 à 20 caractères.
    phone_number: z
      .string()
      .trim()
      .regex(/^(\+?[0-9 .-]{6,20})?$/, 'Numéro de téléphone invalide.'),

    // 12 caractères minimum, comme l'API (recommandation ANSSI).
    // Le plafond de 128 évite des mots de passe très longs qui pourraient alourdir le hachage.
    password: z.string().min(12, '12 caractères minimum.').max(128),

    // Pas de règle ici : la vérification de correspondance se fait dans refine() plus bas.
    confirm: z.string(),
  })
  // refine() ajoute une règle qui porte sur l'objet entier : les deux mots de passe doivent être identiques.
  // path: ['confirm'] attache l'erreur au champ de confirmation plutôt qu'au formulaire en général.
  .refine((data) => data.password === data.confirm, {
    path: ['confirm'],
    message: 'Les deux mots de passe ne correspondent pas.',
  })

// Type TypeScript déduit automatiquement du schéma : évite de le redéfinir à la main.
type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const {
    register,       // relie un champ <input> au formulaire
    handleSubmit,   // n'appelle la fonction fournie que si la validation réussit
    formState: { errors }, // erreurs de validation, champ par champ
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    // phone_number commence à chaîne vide : sinon il serait undefined et la regex ne s'appliquerait pas proprement.
    defaultValues: { phone_number: '' },
  })

  // Gère l'appel à l'API. isPending, isSuccess et error pilotent l'affichage.
  const mutation = useMutation({
    // La confirmation ne sert qu'au contrôle côté navigateur : elle n'est pas envoyée.
    mutationFn: (values: FormValues) =>
      registerAccount({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
        // Envoie undefined (champ omis) plutôt qu'une chaîne vide, ce qui évite de stocker "" en base.
        phone_number: values.phone_number || undefined,
      }),
  })

  return (
    // Fond plein écran, contenu centré verticalement et horizontalement.
    <div className="flex min-h-screen items-center justify-center bg-navy-900 px-4 py-12">
      <main className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-xl sm:p-8">
        <Logo />
        <h1 className="mt-6 text-2xl font-bold">Demander un accès organisateur</h1>

        {/* Après un envoi réussi, on remplace le formulaire par un message de confirmation. */}
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
          // Fragment <> : regroupe plusieurs éléments sans ajouter de balise dans le DOM.
          <>
            <p className="mt-1 text-sm text-navy-500">
              Votre compte sera validé par l'administrateur avant votre première connexion.
            </p>

            {/*
              handleSubmit(valider puis appeler mutate) : la mutation n'est lancée que si le formulaire est valide.
              noValidate désactive la validation HTML native du navigateur, pour laisser Zod gérer les messages.
            */}
            <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="mt-6 space-y-4">
              {/* Deux champs côte à côte sur écran large, empilés sur mobile. */}
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Prénom" required error={errors.first_name?.message}>
                  {/* Field passe props (id, aria-describedby, etc.) pour relier le libellé, le champ et le message d'erreur. Le spread ...props et ...register('first_name') sont fusionnés. */}
                  {(props) => <input {...props} {...register('first_name')} autoComplete="given-name" className={inputClass} />}
                </Field>
                <Field label="Nom" required error={errors.last_name?.message}>
                  {(props) => <input {...props} {...register('last_name')} autoComplete="family-name" className={inputClass} />}
                </Field>
              </div>

              <Field label="Email professionnel" required error={errors.email?.message}>
                {(props) => <input {...props} {...register('email')} type="email" autoComplete="email" className={inputClass} />}
              </Field>

              {/* hint : texte d'aide affiché sous le champ quand il n'y a pas d'erreur. */}
              <Field label="Téléphone" error={errors.phone_number?.message} hint="Facultatif : permet la vérification par SMS.">
                {(props) => <input {...props} {...register('phone_number')} type="tel" autoComplete="tel" className={inputClass} />}
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                {/* autoComplete="new-password" indique au navigateur de proposer un mot de passe fort plutôt que de remplir l'ancien. */}
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

              {/* Erreur renvoyée par l'API (ex. email déjà utilisé), affichée en bas du formulaire. */}
              {mutation.error && <Alert>{mutation.error.message}</Alert>}

              {/* Désactivé pendant l'envoi pour éviter les doubles soumissions. */}
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