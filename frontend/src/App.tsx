/**
 * Plan du site (routes). Chaque groupe partage une mise en page :
 * - pages publiques : PublicLayout
 * - espace organisateur (/espace) : OrganizerLayout, protégé par RequireAuth
 * (Bloc JSDoc : documente la structure des routes pour les autres développeurs.)
 */

// Route : déclare une correspondance URL → composant. Routes : conteneur qui sélectionne la première route qui correspond à l'URL courante.
import { Route, Routes } from 'react-router-dom'

// Composant "garde" : affiche ses enfants si l'utilisateur est connecté, sinon redirige vers /connexion. Avec la prop adminOnly, il exige en plus le rôle administrateur.
import { RequireAuth } from './auth/RequireAuth'

// Mises en page partagées : barre de navigation, pied de page, menu latéral, etc. Chaque layout contient un <Outlet /> où s'affichent les routes enfants.
import { OrganizerLayout, PublicLayout } from './components/layouts'

// Pages réservées aux administrateurs (gestion des utilisateurs et des sauvegardes).
import { BackupsPage } from './pages/admin/BackupsPage'
import { UsersPage } from './pages/admin/UsersPage'

// Pages publiques.
import { CampPage } from './pages/CampPage'     // landing page d'un camp
import { HomePage } from './pages/HomePage'     // accueil
import { LoginPage } from './pages/LoginPage'   // connexion
import { RegisterPage } from './pages/RegisterPage' // inscription
import { NotFoundPage } from './pages/NotFoundPage' // page 404

// Pages de l'espace organisateur.
import { AccountPage } from './pages/organizer/AccountPage'       // compte de l'utilisateur
import { CampFormPage } from './pages/organizer/CampFormPage'     // création/modification d'un camp (formulaire)
import { CampManagePage } from './pages/organizer/CampManagePage' // gestion d'un camp existant
import { DashboardPage } from './pages/organizer/DashboardPage'   // tableau de bord

// Composant racine : retourne l'arbre de routes. Exporté par défaut pour être importé dans main.tsx.
export default function App() {
  return (
    // Conteneur de routes : seule la première route correspondante est rendue.
    <Routes>
      {/* Groupe de routes publiques. Pas de path : la route parente ne consomme aucun segment d'URL.
          element={<PublicLayout />} : cette mise en page entoure toutes les routes enfants. */}
      <Route element={<PublicLayout />}>
        {/* index : correspond à la racine "/" (sans segment supplémentaire). */}
        <Route index element={<HomePage />} />

        {/* :slug est un paramètre dynamique : /camps/ete-2026 → slug = "ete-2026". Lu dans la page via useParams. */}
        <Route path="camps/:slug" element={<CampPage />} />

        {/* Joker "*" : capture toute URL non reconnue. Doit rester en dernier pour ne pas masquer les autres routes. */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      {/* Routes publiques hors layout public : pages d'authentification, sans barre de navigation standard. */}
      <Route path="connexion" element={<LoginPage />} />
      <Route path="inscription" element={<RegisterPage />} />

      {/* Espace organisateur protégé. RequireAuth vérifie la connexion avant d'afficher OrganizerLayout et ses enfants. */}
      <Route
        path="espace"
        element={
          <RequireAuth>
            <OrganizerLayout />
          </RequireAuth>
        }
      >
        {/* Chemins relatifs : ces routes deviennent /espace, /espace/camps/nouveau, etc. */}

        {/* Tableau de bord, affiché sur /espace. */}
        <Route index element={<DashboardPage />} />

        {/* Création d'un camp. "nouveau" est un segment fixe, déclaré avant ":campId" pour ne pas être pris pour un identifiant. */}
        <Route path="camps/nouveau" element={<CampFormPage />} />

        {/* Gestion d'un camp donné : campId est un paramètre dynamique (ex. /espace/camps/12). */}
        <Route path="camps/:campId" element={<CampManagePage />} />

        {/* Modification d'un camp : même formulaire que la création, avec les données pré-remplies. */}
        <Route path="camps/:campId/modifier" element={<CampFormPage />} />

        {/* Compte personnel de l'utilisateur connecté. */}
        <Route path="compte" element={<AccountPage />} />

        {/* Gestion des utilisateurs : accessible uniquement aux administrateurs (adminOnly).
            Une garde imbriquée s'ajoute à celle du parent : il faut être connecté ET admin. */}
        <Route
          path="utilisateurs"
          element={
            <RequireAuth adminOnly>
              <UsersPage />
            </RequireAuth>
          }
        />

        {/* Sauvegardes de la base : également réservées aux administrateurs. */}
        <Route
          path="sauvegardes"
          element={
            <RequireAuth adminOnly>
              <BackupsPage />
            </RequireAuth>
          }
        />
      </Route>
    </Routes>
  )
}