/**
 * Création et modification d'un camp (même formulaire, deux modes).
 * Les règles de validation reprennent celles de l'API : dates cohérentes,
 * un seul âge minimum entre 0 et 99 (vide = tous âges), capacité ≥ 1.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useFieldArray, useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { createCamp, deleteCamp, fetchCamp, updateCamp } from '../../api/endpoints'
import type { Camp, CampInput } from '../../api/types'
import { Alert, Button, Card, Field, inputClass, PageHeader, Spinner } from '../../components/ui'
import { campSchema, type CampFormValues } from '../../lib/campSchema'
import { modalityLabels, statusLabels } from '../../lib/format'

const emptyValues: CampFormValues = {
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  city: '',
  age: null,
  capacity: 20,
  status: 'draft',
  modalities: [],
}

function toFormValues(camp: Camp): CampFormValues {
  return {
    name: camp.name,
    description: camp.description ?? '',
    start_date: camp.start_date,
    end_date: camp.end_date,
    city: camp.city,
    age: camp.age,
    capacity: camp.capacity,
    status: camp.status,
    modalities: camp.modalities,
  }
}

function toPayload(values: CampFormValues): CampInput {
  return { ...values, description: values.description.trim() || null }
}

export function CampFormPage() {
  const { campId } = useParams()
  const isEdit = Boolean(campId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // En création, pas de camp à charger : la requête est désactivée (enabled: false).
  const campQuery = useQuery({
    queryKey: ['camp', campId],
    queryFn: () => fetchCamp(campId!),
    enabled: isEdit,
  })

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CampFormValues>({ resolver: zodResolver(campSchema), defaultValues: emptyValues })
  const modalities = useFieldArray({ control, name: 'modalities' })

  // En modification, on remplit le formulaire dès que le camp est chargé.
  useEffect(() => {
    if (campQuery.data) reset(toFormValues(campQuery.data))
  }, [campQuery.data, reset])

  const save = useMutation({
    mutationFn: (values: CampFormValues) =>
      isEdit ? updateCamp(campId!, toPayload(values)) : createCamp(toPayload(values)),
    onSuccess: (camp) => {
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      // On met directement en cache le camp renvoyé par l'API : la page suivante
      // l'affiche tout de suite, sans nouvel appel réseau.
      queryClient.setQueryData(['camp', camp.id], camp)
      navigate(`/espace/camps/${camp.id}`)
    },
  })

  const remove = useMutation({
    mutationFn: () => deleteCamp(campId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate('/espace')
    },
  })

  if (isEdit && campQuery.isPending) return <Spinner />
  if (isEdit && campQuery.isError) return <Alert>{campQuery.error.message}</Alert>

  const registrations = campQuery.data?.registrations_count ?? 0

  return (
    <>
      <PageHeader
        title={isEdit ? 'Modifier le camp' : 'Nouveau camp'}
        subtitle={isEdit ? campQuery.data?.name : 'La landing page pourra être publiée à l’étape suivante.'}
      />
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
                  // Champ vide -> null ("tous âges") plutôt que NaN.
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
              hint={isEdit ? `${registrations} inscrit(s) : la capacité ne peut pas descendre en dessous.` : undefined}
            >
              {(props) => (
                <input
                  {...props}
                  {...register('capacity', { valueAsNumber: true })}
                  type="number"
                  min={Math.max(1, registrations)}
                  className={inputClass}
                />
              )}
            </Field>
          </div>
        </Card>

        <Card>
          <fieldset>
            <legend className="text-lg font-bold">Modalités d'éligibilité et options</legend>
            <p className="mt-1 text-sm text-navy-500">Ex. « Niveau collège minimum », « Repas inclus ».</p>
            <ul className="mt-4 space-y-3">
              {modalities.fields.map((field, index) => (
                <li key={field.id} className="grid gap-2 sm:grid-cols-[10rem_1fr_auto] sm:items-start">
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
                      aria-invalid={Boolean(errors.modalities?.[index]?.label)}
                      className={inputClass}
                    />
                    {errors.modalities?.[index]?.label && (
                      <p className="mt-1 text-xs font-medium text-coral-700">{errors.modalities[index]?.label?.message}</p>
                    )}
                  </div>
                  <Button type="button" variant="ghost" onClick={() => modalities.remove(index)}>
                    Retirer<span className="sr-only"> la modalité {index + 1}</span>
                  </Button>
                </li>
              ))}
            </ul>
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
            <span />
          )}
          <div className="flex gap-3">
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
