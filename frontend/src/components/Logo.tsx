// Link : lien de navigation interne de React Router (pas de rechargement de page).
import { Link } from 'react-router-dom'

/** Logo CampOrga : une tente stylisée (création originale) + le nom. */
// to : destination du lien (accueil par défaut). light : version claire pour fond sombre.
export function Logo({ to = '/', light = false }: { to?: string; light?: boolean }) {
  return (
    // inline-flex : le lien s'adapte à la taille de son contenu. aria-label : nom accessible
    // unique pour le lecteur d'écran, qui remplace la lecture de l'icône et du texte séparément.
    <Link to={to} className="inline-flex items-center gap-2 rounded-lg" aria-label="CampOrga, accueil">
      {/* Icône : décorative, cachée aux lecteurs d'écran (aria-hidden) car le nom est déjà porté par le lien. */}
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        {/* Fond arrondi couleur corail. */}
        <rect width="32" height="32" rx="9" className="fill-coral-600" />
        {/* Toile de tente, porte ouverte et petit fanion */}
        {/* Triangle blanc : la toile de la tente. */}
        <path d="M5 25 16 8l11 17H5Z" fill="white" />
        {/* Triangle corail à la base : la porte, découpée dans la toile. */}
        <path d="M12.5 25 16 18.5l3.5 6.5h-7Z" className="fill-coral-600" />
        {/* Mât et fanion : tracé en contour, sans remplissage. */}
        <path d="M16 8V4.5l4 1.6-4 1.6" fill="none" stroke="white" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
      {/* Nom affiché à côté de l'icône. Couleur blanche sur fond sombre, bleu nuit sinon. */}
      <span className={`font-display text-lg font-bold ${light ? 'text-white' : 'text-navy-900'}`}>CampOrga</span>
    </Link>
  )
}