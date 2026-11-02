/**
 * Mises en page : partie publique (visiteurs) et espace organisateur.
 * <Outlet /> est l'emplacement où React Router affiche la page courante.
 */
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { isSuperAdmin, useAuth } from '../auth/useAuth'
import { roleLabels } from '../lib/format'
import { Logo } from './Logo'

/** Lien d'évitement : permet aux utilisateurs clavier de sauter la navigation. */
function SkipLink() {
  return (
    <a
      href="#contenu"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
    >
      Aller au contenu
    </a>
  )
}

export function PublicLayout() {
  const { user } = useAuth()
  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink />
      <header className="sticky top-0 z-30 border-b border-navy-100/70 bg-sand-50/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo />
          <NavLink
            to={user ? '/espace' : '/connexion'}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-navy-700 hover:bg-navy-50"
          >
            {user ? 'Mon espace' : 'Espace organisateur'}
          </NavLink>
        </div>
      </header>
      <main id="contenu" className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-navy-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-navy-500 sm:flex-row sm:justify-between sm:px-6">
          <p>© {new Date().getFullYear()} CampOrga – Summer camps de code</p>
          <p>Vos données d'inscription servent uniquement à l'organisation du camp.</p>
        </div>
      </footer>
    </div>
  )
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  `block rounded-xl px-3 py-2 text-sm font-medium transition ${
    isActive ? 'bg-white/15 text-white' : 'text-navy-100 hover:bg-white/10 hover:text-white'
  }`

export function OrganizerLayout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const links = (
    <>
      <NavLink to="/espace" end className={navClass} onClick={() => setMenuOpen(false)}>
        Tableau de bord
      </NavLink>
      <NavLink to="/espace/camps/nouveau" className={navClass} onClick={() => setMenuOpen(false)}>
        Nouveau camp
      </NavLink>
      {isSuperAdmin(user?.role) && (
        <>
          <p className="px-3 pt-4 text-xs font-semibold uppercase tracking-wider text-navy-100/70">Administration</p>
          <NavLink to="/espace/utilisateurs" className={navClass} onClick={() => setMenuOpen(false)}>
            Utilisateurs
          </NavLink>
          <NavLink to="/espace/sauvegardes" className={navClass} onClick={() => setMenuOpen(false)}>
            Sauvegardes
          </NavLink>
        </>
      )}
      <NavLink to="/" className={navClass} onClick={() => setMenuOpen(false)}>
        Voir le site public
      </NavLink>
    </>
  )

  return (
    <div className="min-h-screen lg:flex">
      <SkipLink />
      {/* Barre latérale (ordinateur) ou bandeau + menu repliable (mobile) */}
      <aside className="bg-navy-900 text-white lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex items-center justify-between px-4 py-4 lg:px-5 lg:py-6">
          <Logo to="/espace" light />
          <button
            type="button"
            className="rounded-lg p-2 text-navy-100 hover:bg-white/10 lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="menu-espace"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="sr-only">{menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}</span>
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              {menuOpen ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
        <nav
          id="menu-espace"
          aria-label="Espace organisateur"
          className={`${menuOpen ? 'block' : 'hidden'} space-y-1 px-3 pb-4 lg:block lg:flex-1`}
        >
          {links}
        </nav>
        <div className={`${menuOpen ? 'block' : 'hidden'} border-t border-white/10 px-5 py-4 lg:block`}>
          <p className="truncate text-sm font-medium">{user?.first_name ?? user?.email}</p>
          <p className="text-xs text-navy-100/80">{user ? roleLabels[user.role] : ''}</p>
          <button type="button" onClick={logout} className="mt-3 text-sm font-semibold text-coral-400 hover:underline">
            Se déconnecter
          </button>
        </div>
      </aside>
      <main id="contenu" className="flex-1 px-4 py-6 sm:px-6 lg:ml-64 lg:px-10 lg:py-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
