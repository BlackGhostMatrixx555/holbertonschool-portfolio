/**
 * Création et modification d'un camp (même formulaire, deux modes).
 * Les règles de validation reprennent celles de l'API : dates cohérentes,
 * âge minimum ≤ âge maximum, capacité ≥ 1.
 */

// zodResolver : relie le schéma Zod (campSchema) à react-hook-form.
import { zodResolver } from '@hookform/resolvers/zod'

// useMutation : écriture (création, modification, suppression) avec suivi d'état.
// useQuery : lecture avec cache. useQueryClient : accès au cache pour le mettre à jour ou l'invalider.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// useEffect : effet de bord, ici le remplissage du formulaire au chargement du camp.
import { useEffect } from 'react'

// useFieldArray : gère une liste de champs dynamique (ajout, suppression de modalités).
// useForm : gestion du formulaire (valeurs, erreurs, soumission).
import { useFieldArray, useForm } from 'react-hook-form'

// useNavigate : navigation programmatique. useParams : lit l'id du camp dans l'URL.
import { useNavigate, useParams } from 'react-router-dom'

// Fonctions d'appel à l'API.
import { createCamp, deleteCamp, fetchCamp, updateCamp } from '../../api/endpoints'

// Types : Camp (données reçues), CampInput (données envoyées).
import type { Camp, CampInput } from '../../api/types'

// Composants d'interface partagés.
import { Alert, Button, Card, Field, inputClass, PageHeader, Spinner } from '../../components/ui'

// campSchema : schéma de validation. CampFormValues : type TypeScript déduit de ce schéma.
import { campSchema, type CampFormValues } from '../../lib/campSchema'

// Libellés traduits pour les modalités et les statuts.
import { modalityLabels, statusLabels } from '../../lib/format'

// Valeurs initiales d'un formulaire vide (mode création).
const emptyValues: CampFormValues = {
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  city: '',
  age: null, // null = ouvert à tous les âges
  capacity: 20,
  status: 'draft', // un nouveau camp n'est pas publié par défaut
  modalities: [],
}

// Convertit un camp reçu de l'API en valeurs de formulaire.
// Le principal écart : la description peut être null côté API, mais le champ texte attend une chaîne.
function toFormValues(camp: Camp): CampFormValues {
  return {
    name: camp.name,
    description: camp.description ?? '', // null -> chaîne vide
    start_date: camp.start_date,
    end_date: camp.end_date,
    city: camp.city,
    age: camp.age,
    capacity: camp.capacity,
    status: camp.status,
    modalities: camp.modalities,
  }
}

// Convertit les valeurs du formulaire en données envoyées à l'API.
// Une description vide devient null, ce que l'API attend pour « pas de description ».
function toPayload(values: CampFormValues): CampInput {
  return { ...values, description: values.description.trim() || null }
}

export function CampFormPage() {
  // Présence d'un campId dans l'URL : mode modification. Sinon, mode création.
  const { campId } = useParams()
  const isEdit = Boolean(campId)

  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Chargement du camp, uniquement en mode modification.
  // enabled: false désactive la requête en création. campId! : l'assertion est sûre car enabled garantit sa présence.
  const campQuery = useQuery({
    queryKey: ['camp', campId],
    queryFn: () => fetchCamp(campId!),
    enabled: isEdit,
  })

  // Initialisation du formulaire avec le schéma de validation et les valeurs vides.
  // Les valeurs réelles sont injectées plus tard par reset (voir useEffect).
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CampFormValues>({ resolver: zodResolver(campSchema), defaultValues: emptyValues })

  // Liste dynamique des modalités, liée au champ "modalities" du formulaire.
  const modalities = useFieldArray({ control, name: 'modalities' })

  // En modification, on remplit le formulaire dès que le camp est chargé.
  // reset remplace toutes les valeurs. Le tableau de dépendances relance l'effet quand les données arrivent.
  useEffect(() => {
    if (campQuery.data) reset(toFormValues(campQuery.data))
  }, [campQuery.data, reset])

  // Enregistrement : création ou modification selon le mode.
  const save = useMutation({
    mutationFn: (values: CampFormValues) =>
      isEdit ? updateCamp(campId!, toPayload(values)) : createCamp(toPayload(values)),
    onSuccess: (camp) => {
      // Invalidation des listes qui affichent les camps.
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      // Mise à jour directe du cache du camp, sans nouvel appel réseau.
      queryClient.setQueryData(['camp', camp.id], camp)
      // Retour sur la page de gestion du camp (le nouveau camp en création, le même en modification).
      navigate(`/espace/camps/${camp.id}`)
    },
  })

  // Suppression du camp. Uniquement en mode modification (campId! est donc présent).
  const remove = useMutation({
    mutationFn: () => deleteCamp(campId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate('/espace')
    },
  })

  // En modification, on attend le chargement avant d'afficher le formulaire.
  if (isEdit && campQuery.isPending) return <Spinner />
  if (isEdit && campQuery.isError) return <Alert>{campQuery.error.message}</Alert>

  // Nombre d'inscrits, utilisé pour borner la capacité minimale. 0 en création.
  const registrations = campQuery.data?.registrations_count ?? 0

  return (
    <>
      <PageHeader
        title={isEdit ? 'Modifier le camp' : 'Nouveau camp'}
        subtitle={isEdit ? campQuery.data?.name : 'La landing page pourra être publiée à l’étape suivante.'}
      />

      {/* handleSubmit valide puis appelle save.mutate avec les valeurs. noValidate : la validation est gérée par Zod. */}
      <form onSubmit={handleSubmit((values) => save.mutate(values))} noValidate className="space-y-6">

        <Card>
          <h2 className="mb-4 text-lg font-bold">Informations générales</h2>
          <div className="space-y-4">
            <Field label="Nom du camp" required error={errors.name?.message}>
              {(props) => <input {...props} {...register('name')} className={inputClass} />}
            </Field>
            <Field label="Description" error={errors.description?.message} hint="Programme, activités, ce qu'on va apprendre.">
              {(props) => <textarea {...props} {...register('description')} rows={5} className={inputClass} />}
            </Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Ville" required error={errors.city?.message}>
                {(props) => <input {...props} {...register('city')} className={inputClass} />}
              </Field>
              <Field label="Début" required error={errors.start_date?.message}>
                {(props) => <input {...props} {...register('start_date')} type="date" className={inputClass} />}
              </Field>
              <Field label="Fin" required error={errors.end_date?.message}>
                {(props) => <input {...props} {...register('end_date')} type="date" className={inputClass} />}
              </Field>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-bold">Participants</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Âge minimum" error={errors.age?.message} hint="Laisser vide : ouvert à tous les âges.">
              {(props) => (
                <input
                  {...props}
                  // setValueAs convertit la saisie : vide ou null -> null ("tous âges"), sinon nombre.
                  // Sans cela, un champ vide donnerait NaN.
                  {...register('age', { setValueAs: (value) => (value === '' || value === null ? null : Number(value)) })}
                  type="number"
                  min={0}
                  max={99}
                  placeholder="Ex. 12"
                  className={inputClass}
                />
              )}
            </Field>
            <Field
              label="Capacité"
              required
              error={errors.capacity?.message}
              // En modification, on signale que la capacité ne peut pas descendre sous le nombre d'inscrits.
              hint={isEdit ? `${registrations} inscrit(s) : la capacité ne peut pas descendre en dessous.` : undefined}
            >
              {(props) => (
                <input
                  {...props}
                  // valueAsNumber : convertit la saisie en nombre directement.
                  {...register('capacity', { valueAsNumber: true })}
                  type="number"
                  // min côté HTML : au moins 1, et au moins le nombre d'inscrits déjà présents.
                  min={Math.max(1, registrations)}
                  className={inputClass}
                />
              )}
            </Field>
          </div>
        </Card>

        <Card>
          {/* fieldset + legend : regroupe les champs liés pour les lecteurs d'écran. */}
          <fieldset>
            <legend className="text-lg font-bold">Modalités d'éligibilité et options</legend>
            <p className="mt-1 text-sm text-navy-500">Ex. « Niveau collège minimum », « Repas inclus ».</p>
            <ul className="mt-4 space-y-3">
              {/* fields : liste courante des modalités. field.id est une clé stable générée par useFieldArray. */}
              {modalities.fields.map((field, index) => (
                <li key={field.id} className="grid gap-2 sm:grid-cols-[10rem_1fr_auto] sm:items-start">
                  {/* Libellé masqué visuellement : le select n'a pas de label visible à côté de lui. */}
                  <label className="sr-only" htmlFor={`modality-type-${index}`}>
                    Type de la modalité {index + 1}
                  </label>
                  <select id={`modality-type-${index}`} {...register(`modalities.${index}.type`)} className={inputClass}>
                    {Object.entries(modalityLabels).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>

                  <div>
                    <label className="sr-only" htmlFor={`modality-label-${index}`}>
                      Description de la modalité {index + 1}
                    </label>
                    <input
                      id={`modality-label-${index}`}
                      {...register(`modalities.${index}.label`)}
                      // aria-invalid signale l'erreur aux lecteurs d'écran.
                      aria-invalid={Boolean(errors.modalities?.[index]?.label)}
                      className={inputClass}
                    />
                    {errors.modalities?.[index]?.label && (
                      <p className="mt-1 text-xs font-medium text-coral-700">{errors.modalities[index]?.label?.message}</p>
                    )}
                  </div>

                  {/* Bouton de suppression de la ligne. */}
                  <Button type="button" variant="ghost" onClick={() => modalities.remove(index)}>
                    Retirer<span className="sr-only"> la modalité {index + 1}</span>
                  </Button>
                </li>
              ))}
            </ul>
            {/* Ajoute une modalité vide, avec un type par défaut. */}
            <Button
              type="button"
              variant="secondary"
              className="mt-3"
              onClick={() => modalities.append({ type: 'education_level', label: '' })}
            >
              + Ajouter une modalité
            </Button>
          </fieldset>
        </Card>

        <Card>
          <Field label="Statut" hint="La publication se fait aussi depuis l'onglet « Landing page » du camp.">
            {(props) => (
              <select {...props} {...register('status')} className={`${inputClass} sm:max-w-xs`}>
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            )}
          </Field>
        </Card>

        {save.error && <Alert>{save.error.message}</Alert>}
        {remove.error && <Alert>{remove.error.message}</Alert>}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
          {/* Bouton de suppression : uniquement en modification. Une confirmation navigateur précède l'action. */}
          {isEdit ? (
            <Button
              type="button"
              variant="danger"
              disabled={remove.isPending}
              onClick={() => {
                if (window.confirm('Supprimer ce camp ? Ses inscriptions seront aussi supprimées.')) remove.mutate()
              }}
            >
              Supprimer le camp
            </Button>
          ) : (
            // Espace vide pour garder la mise en page (les boutons restent à droite).
            <span />
          )}

          <div className="flex gap-3">
            {/* navigate(-1) : retour à la page précédente dans l'historique. */}
            <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
              Annuler
            </Button>
            <Button type="submit" disabled={save.isPending}>
              {save.isPending ? 'Enregistrement…' : isEdit ? 'Enregistrer' : 'Créer le camp'}
            </Button>
          </div>
        </div>
      </form>
    </>
  )
}