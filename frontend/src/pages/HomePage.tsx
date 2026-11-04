/** Page d'accueil : présentation et liste des camps publiés. */

// useQuery : hook de TanStack Query qui récupère des données, les met en cache et gère les états de chargement et d'erreur.
import { useQuery } from '@tanstack/react-query'

// Fonction d'appel à l'API qui renvoie la liste des camps publiés.
import { fetchPublicCamps } from '../api/endpoints'

// Carte d'affichage d'un camp (nom, dates, places, lien vers la page du camp).
import { CampCard } from '../components/CampCard'

// Composants d'interface partagés : alerte, état vide, indicateur de chargement.
import { Alert, EmptyState, Spinner } from '../components/ui'

export function HomePage() {
  // Déclaration de la requête. queryKey identifie le cache (deux pages utilisant la même clé partagent les données).
  // queryFn est la fonction exécutée pour récupérer les données.
  // L'objet retourné contient isPending, isError, error et data, utilisés plus bas pour choisir l'affichage.
  const camps = useQuery({ queryKey: ['public-camps'], queryFn: fetchPublicCamps })

  return (
    // Fragment : regroupe les deux sections sans ajouter d'élément superflu dans le DOM.
    <>
      {/* Bandeau d'accroche */}
      <section className="relative overflow-hidden bg-navy-900 text-white">
        {/* aria-hidden="true" : ces éléments sont purement décoratifs, les lecteurs d'écran les ignorent. */}
        <div aria-hidden="true" className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-coral-600/30 blur-3xl" />
        <div aria-hidden="true" className="absolute -bottom-32 left-10 h-72 w-72 rounded-full bg-winter/30 blur-3xl" />

        {/* relative : place le contenu au-dessus des cercles décoratifs (position absolue). */}
        <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <p className="text-sm font-semibold uppercase tracking-widest text-coral-400">Apprendre · Créer · Partager</p>

          {/* Titre principal de la page, unique et de niveau h1. */}
          <h1 className="mt-3 max-w-2xl text-4xl font-bold leading-tight sm:text-5xl">
            Des summer camps pour découvrir le code.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-navy-100">
            Programmation, web, robotique : choisissez votre camp et inscrivez-vous en moins d'une minute.
          </p>

          {/* Lien d'ancre : fait défiler la page jusqu'à la section d'id "camps", sans quitter la page. */}
          <a
            href="#camps"
            className="mt-8 inline-flex rounded-xl bg-coral-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-coral-700"
          >
            Voir les camps
          </a>
        </div>
      </section>

      {/* Liste des camps. scroll-mt-20 compense la barre de navigation fixe lors du défilement vers l'ancre. */}
      <section id="camps" aria-labelledby="camps-title" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-12 sm:px-6">
        {/* aria-labelledby relie la section à son titre, utile aux lecteurs d'écran. */}
        <h2 id="camps-title" className="text-2xl font-bold sm:text-3xl">
          Les prochains camps
        </h2>

        <div className="mt-6">
          {/* Trois états possibles, affichés en fonction de l'état de la requête. */}

          {/* 1. Chargement en cours. */}
          {camps.isPending && <Spinner label="Chargement des camps…" />}

          {/* 2. Erreur réseau ou serveur. */}
          {camps.isError && <Alert>{camps.error.message}</Alert>}

          {/* 3. Succès mais liste vide. */}
          {camps.data?.length === 0 && (
            <EmptyState title="Aucun camp pour le moment">Revenez bientôt, de nouvelles sessions arrivent.</EmptyState>
          )}

          {/* 4. Succès avec des camps : affichage de la grille. */}
          {/* camps.data && ... garantit que data existe avant de lire length. */}
          {camps.data && camps.data.length > 0 && (
            // Liste sémantique (ul/li) : les lecteurs d'écran annoncent le nombre d'éléments.
            <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {camps.data.map((camp) => (
                // key : identifiant stable permettant à React de suivre chaque élément lors des mises à jour.
                // flex : étire la carte à la hauteur de la ligne, pour que toutes les cartes aient la même taille.
                <li key={camp.id} className="flex">
                  <CampCard camp={camp} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  )
}