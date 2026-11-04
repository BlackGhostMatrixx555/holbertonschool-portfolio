/**
 * Mises en page : partie publique (visiteurs) et espace organisateur.
 * <Outlet /> est l'emplacement où React Router affiche la page courante.
 */
// useState : état local (menu mobile ouvert ou fermé).
import { useState } from 'react'
// NavLink : lien qui sait indiquer s'il correspond à la page active. Outlet : emplacement des pages enfants.
import { NavLink, Outlet } from 'react-router-dom'
// isSuperAdmin : vérifie le rôle. useAuth : accès à l'utilisateur connecté et à la déconnexion.
import { isSuperAdmin, useAuth } from '../auth/useAuth'
// Libellés lisibles des rôles (ex. « Organisateur »).
import { roleLabels } from '../lib/format'
import { Logo } from './Logo'

/** Lien d'évitement : permet aux utilisateurs clavier de sauter la navigation. */
function SkipLink() {
  return (
    // Lien invisible tant qu'il n'a pas le focus (sr-only), puis affiché en haut à gauche
    // quand on le sélectionne au clavier avec la touche Tab. Il renvoie vers l'élément id="contenu".
    <a
      href="#contenu"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
    >
      Aller au contenu
    </a>
  )
}

export function PublicLayout() {
  // Utilisateur connecté éventuel, pour adapter le lien d'espace.
  const { user } = useAuth()
  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink />
      {/* En-tête collant en haut de page, avec effet de flou sur le fond. */}
      <header className="sticky top-0 z-30 border-b border-navy-100/70 bg-sand-50/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo />
          {/* Vers l'espace si connecté, sinon vers la page de connexion. */}
          <NavLink
            to={user ? '/espace' : '/connexion'}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-navy-700 hover:bg-navy-50"
          >
            {user ? 'Mon espace' : 'Espace organisateur'}
          </NavLink>
        </div>
      </header>
      {/* id="contenu" : cible du lien d'évitement. flex-1 : occupe la hauteur restante. */}
      <main id="contenu" className="flex-1">
        {/* Emplacement de la page visitée (accueil, camp, connexion…). */}
        <Outlet />
      </main>
      <footer className="border-t border-navy-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-navy-500 sm:flex-row sm:justify-between sm:px-6">
          {/* Année calculée à chaque rendu, donc toujours à jour. */}
          <p>© {new Date().getFullYear()} CampOrga – Summer camps de code</p>
          <p>Vos données d'inscription servent uniquement à l'organisation du camp.</p>
        </div>
      </footer>
    </div>
  )
}

// Style des liens de la navigation organisateur : fond clair si la page est active.
// Fonction qui reçoit l'état isActive fourni par NavLink.
const navClass = ({ isActive }: { isActive: boolean }) =>
  `block rounded-xl px-3 py-2 text-sm font-medium transition ${
    isActive ? 'bg-white/15 text-white' : 'text-navy-100 hover:bg-white/10 hover:text-white'
  }`

export function OrganizerLayout() {
  // Utilisateur, fonction de déconnexion.
  const { user, logout } = useAuth()
  // Menu mobile ouvert ou fermé.
  const [menuOpen, setMenuOpen] = useState(false)

  // Liens de navigation, réutilisés au même endroit dans le JSX. Fermer le menu mobile à chaque clic.
  const links = (
    <>
      {/* end : ce lien n'est actif que sur /espace exactement, pas sur ses sous-pages. */}
      <NavLink to="/espace" end className={navClass} onClick={() => setMenuOpen(false)}>
        Tableau de bord
      </NavLink>
      <NavLink to="/espace/camps/nouveau" className={navClass} onClick={() => setMenuOpen(false)}>
        Nouveau camp
      </NavLink>
      <NavLink to="/espace/compte" className={navClass} onClick={() => setMenuOpen(false)}>
        Mon compte
      </NavLink>
      {/* Section réservée au super administrateur. */}
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
    // lg:flex : sur grand écran, barre latérale et contenu côte à côte.
    <div className="min-h-screen lg:flex">
      <SkipLink />
      {/* Barre latérale (ordinateur) ou bandeau + menu repliable (mobile) */}
      <aside className="bg-navy-900 text-white lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex items-center justify-between px-4 py-4 lg:px-5 lg:py-6">
          <Logo to="/espace" light />
          {/* Bouton de menu, visible seulement sur mobile (lg:hidden).
              aria-expanded et aria-controls indiquent l'état du menu aux lecteurs d'écran. */}
          <button
            type="button"
            className="rounded-lg p-2 text-navy-100 hover:bg-white/10 lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="menu-espace"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {/* Texte réservé aux lecteurs d'écran. */}
            <span className="sr-only">{menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}</span>
            {/* Icône : croix quand le menu est ouvert, trois barres sinon. aria-hidden : icône décorative. */}
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              {menuOpen ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
        {/* Sur mobile, la navigation n'apparaît que si menuOpen est vrai. Sur grand écran, elle reste visible. */}
        <nav
          id="menu-espace"
          aria-label="Espace organisateur"
          className={`${menuOpen ? 'block' : 'hidden'} space-y-1 px-3 pb-4 lg:block lg:flex-1`}
        >
          {links}
        </nav>
        {/* Bloc utilisateur et déconnexion, même logique d'affichage que la navigation. */}
        <div className={`${menuOpen ? 'block' : 'hidden'} border-t border-white/10 px-5 py-4 lg:block`}>
          {/* truncate : coupe le nom trop long plutôt que de casser la mise en page. */}
          <p className="truncate text-sm font-medium">{user?.first_name ?? user?.email}</p>
          <p className="text-xs text-navy-100/80">{user ? roleLabels[user.role] : ''}</p>
          <button type="button" onClick={logout} className="mt-3 text-sm font-semibold text-coral-400 hover:underline">
            Se déconnecter
          </button>
        </div>
      </aside>
      {/* lg:ml-64 : décale le contenu pour laisser la place à la barre latérale fixe. */}
      <main id="contenu" className="flex-1 px-4 py-6 sm:px-6 lg:ml-64 lg:px-10 lg:py-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}