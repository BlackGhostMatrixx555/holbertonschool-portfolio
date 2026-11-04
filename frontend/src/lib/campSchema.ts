/**
 * Règles de validation du formulaire de camp (zod).
 * Elles reprennent celles de l'API (app/schemas/camp.py) pour un retour immédiat,
 * mais c'est l'API qui reste la référence : elle revalide tout.
 */

// z : bibliothèque de validation de schémas (types et règles au même endroit).
import { z } from 'zod'

// Schéma du formulaire de camp. Chaque champ décrit son type et ses règles.
export const campSchema = z
  .object({
    // Nom : espaces supprimés en début et fin, obligatoire, 200 caractères maximum.
    name: z.string().trim().min(1, 'Le nom est obligatoire.').max(200),

    // Description facultative (chaîne vide acceptée), 5000 caractères maximum.
    description: z.string().max(5000, '5000 caractères maximum.'),

    // Dates saisies au format « AAAA-MM-JJ » (champ date HTML). Simplement non vides ici ;
    // la cohérence entre les deux dates est vérifiée plus bas.
    start_date: z.string().min(1, 'La date de début est obligatoire.'),
    end_date: z.string().min(1, 'La date de fin est obligatoire.'),

    // Ville obligatoire, 100 caractères maximum.
    city: z.string().trim().min(1, 'La ville est obligatoire.').max(100),

    // Âge minimum requis : entier entre 0 et 99, ou null si le champ est vide (= tous âges).
    // error : message affiché si la valeur n'est pas un nombre (par exemple une saisie non numérique).
    age: z.number({ error: 'Âge invalide.' }).int().min(0, 'Âge invalide.').max(99, 'Âge invalide.').nullable(),

    // Capacité : entier entre 1 et 10000.
    capacity: z
      .number({ error: 'Indiquez une capacité.' })
      .int()
      .min(1, 'Au moins 1 place.')
      .max(10000),

    // Statut limité aux trois valeurs prévues. Toute autre valeur est rejetée.
    status: z.enum(['draft', 'published', 'archived']),

    // Liste de modalités (conditions, options, inclusions), 20 éléments maximum.
    // Chaque modalité a un type parmi une liste fermée et un libellé non vide.
    modalities: z
      .array(
        z.object({
          type: z.enum(['age_restriction', 'education_level', 'included', 'option', 'other']),
          label: z.string().trim().min(1, 'Décrivez la modalité.').max(200),
        }),
      )
      .max(20),
  })
  // Règle portant sur deux champs : vérifiée seulement quand l'objet entier est validé.
  // La condition accepte la fin si l'une des dates est vide (ce cas est déjà signalé par les règles ci-dessus).
  // Comme les dates sont au format AAAA-MM-JJ, la comparaison de chaînes suit l'ordre chronologique.
  // path : l'erreur est rattachée au champ end_date pour être affichée à côté de lui.
  .refine((data) => !data.start_date || !data.end_date || data.end_date >= data.start_date, {
    path: ['end_date'],
    message: 'La fin doit être après le début.',
  })

// Type TypeScript déduit du schéma : évite de décrire deux fois la même forme de données.
export type CampFormValues = z.infer<typeof campSchema>