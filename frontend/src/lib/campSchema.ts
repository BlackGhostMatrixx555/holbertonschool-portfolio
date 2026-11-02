/**
 * Règles de validation du formulaire de camp (zod).
 * Elles reprennent celles de l'API (app/schemas/camp.py) pour un retour immédiat,
 * mais c'est l'API qui reste la référence : elle revalide tout.
 */
import { z } from 'zod'

const ageField = z
  .number({ invalid_type_error: 'Indiquez un âge.' })
  .int()
  .min(0, 'Âge invalide.')
  .max(99, 'Âge invalide.')

export const campSchema = z
  .object({
    name: z.string().trim().min(1, 'Le nom est obligatoire.').max(200),
    description: z.string().max(5000, '5000 caractères maximum.'),
    start_date: z.string().min(1, 'La date de début est obligatoire.'),
    end_date: z.string().min(1, 'La date de fin est obligatoire.'),
    city: z.string().trim().min(1, 'La ville est obligatoire.').max(100),
    min_age: ageField,
    max_age: ageField,
    capacity: z
      .number({ invalid_type_error: 'Indiquez une capacité.' })
      .int()
      .min(1, 'Au moins 1 place.')
      .max(10000),
    status: z.enum(['draft', 'published', 'archived']),
    modalities: z
      .array(
        z.object({
          type: z.enum(['age_restriction', 'education_level', 'included', 'option', 'other']),
          label: z.string().trim().min(1, 'Décrivez la modalité.').max(200),
        }),
      )
      .max(20),
  })
  // Règles portant sur deux champs : l'erreur est rattachée au second champ.
  .refine((data) => !data.start_date || !data.end_date || data.end_date >= data.start_date, {
    path: ['end_date'],
    message: 'La fin doit être après le début.',
  })
  .refine((data) => data.min_age <= data.max_age, {
    path: ['max_age'],
    message: "L'âge maximum doit être supérieur ou égal à l'âge minimum.",
  })

export type CampFormValues = z.infer<typeof campSchema>
