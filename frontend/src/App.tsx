/**
 * Plan du site (routes). Chaque groupe partage une mise en page :
 * - pages publiques : PublicLayout
 * - espace organisateur (/espace) : OrganizerLayout, protégé par RequireAuth
 */
import { Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth/RequireAuth'
import { OrganizerLayout, PublicLayout } from './components/layouts'
import { BackupsPage } from './pages/admin/BackupsPage'
import { UsersPage } from './pages/admin/UsersPage'
import { CampPage } from './pages/CampPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { AccountPage } from './pages/organizer/AccountPage'
import { CampFormPage } from './pages/organizer/CampFormPage'
import { CampManagePage } from './pages/organizer/CampManagePage'
import { DashboardPage } from './pages/organizer/DashboardPage'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="camps/:slug" element={<CampPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route path="connexion" element={<LoginPage />} />
      <Route path="inscription" element={<RegisterPage />} />

      <Route
        path="espace"
        element={
          <RequireAuth>
            <OrganizerLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="camps/nouveau" element={<CampFormPage />} />
        <Route path="camps/:campId" element={<CampManagePage />} />
        <Route path="camps/:campId/modifier" element={<CampFormPage />} />
        <Route path="compte" element={<AccountPage />} />
        <Route
          path="utilisateurs"
          element={
            <RequireAuth adminOnly>
              <UsersPage />
            </RequireAuth>
          }
        />
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
