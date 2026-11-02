import { Link } from 'react-router-dom'

/** Logo CampOrga : une tente stylisée (création originale) + le nom. */
export function Logo({ to = '/', light = false }: { to?: string; light?: boolean }) {
  return (
    <Link to={to} className="inline-flex items-center gap-2 rounded-lg" aria-label="CampOrga, accueil">
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <rect width="32" height="32" rx="9" className="fill-coral-600" />
        {/* Toile de tente, porte ouverte et petit fanion */}
        <path d="M5 25 16 8l11 17H5Z" fill="white" />
        <path d="M12.5 25 16 18.5l3.5 6.5h-7Z" className="fill-coral-600" />
        <path d="M16 8V4.5l4 1.6-4 1.6" fill="none" stroke="white" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
      <span className={`font-display text-lg font-bold ${light ? 'text-white' : 'text-navy-900'}`}>CampOrga</span>
    </Link>
  )
}
