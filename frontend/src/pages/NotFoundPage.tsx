// LinkButton : bouton stylé qui est un lien de navigation interne (React Router), sans rechargement de page.
// Importé depuis les composants UI partagés pour garder un aspect cohérent avec le reste du site.
import { LinkButton } from '../components/ui'

// Page affichée lorsqu'aucune route ne correspond à l'URL demandée.
// Exportée nommée : elle peut être importée directement dans le plan du site (routes).
export function NotFoundPage() {
  return (
    // Conteneur centré : mx-auto centre horizontalement, max-w-xl limite la largeur, py-24 ajoute de l'espace vertical.
    // px-4 garantit une marge sur petit écran, text-center centre le texte.
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      {/* Code d'erreur affiché en grand, avec la couleur d'accent corail. font-display utilise la police de titre. */}
      <p className="font-display text-6xl font-bold text-coral-600">404</p>

      {/* Titre principal de la page : un h1 par page est une bonne pratique pour l'accessibilité et le référencement. */}
      <h1 className="mt-4 text-2xl font-bold">Page introuvable</h1>

      {/* Explication courte : l'adresse est invalide ou la page a changé d'emplacement. */}
      <p className="mt-2 text-navy-500">Cette page n'existe pas ou a été déplacée.</p>

      {/* Lien de retour vers la page d'accueil, pour que l'utilisateur ne reste pas bloqué. */}
      <LinkButton to="/" className="mt-6">
        Retour à l'accueil
      </LinkButton>
    </div>
  )
}