/** Page 404 : affichée pour toute URL qui ne correspond à aucune route (voir App.tsx). */
import { LinkButton } from '../components/ui'

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="font-display text-6xl font-bold text-coral-600">404</p>
      <h1 className="mt-4 text-2xl font-bold">Page introuvable</h1>
      <p className="mt-2 text-navy-500">Cette page n'existe pas ou a été déplacée.</p>
      <LinkButton to="/" className="mt-6">
        Retour à l'accueil
      </LinkButton>
    </div>
  )
}
