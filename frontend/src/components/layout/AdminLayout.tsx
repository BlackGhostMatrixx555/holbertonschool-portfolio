import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function AdminLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-navy text-white flex">
      <aside className="w-64 bg-navy-dark p-6 flex flex-col">
        <h1 className="text-2xl font-display font-bold mb-8">CampOrga Admin</h1>
        <nav className="space-y-2 flex-1">
          <Link to="/admin" className="block p-2 rounded hover:bg-white/10">
            Dashboard
          </Link>
          <Link to="/admin/users" className="block p-2 rounded hover:bg-white/10">
            Utilisateurs
          </Link>
          <Link to="/admin/backups" className="block p-2 rounded hover:bg-white/10">
            Backups
          </Link>
        </nav>
        <div className="border-t border-white/20 pt-4">
          <p className="text-sm text-gray-300 mb-2">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="text-coral text-sm font-semibold hover:underline"
          >
            Déconnexion
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 bg-surface text-ink">
        <Outlet />
      </main>
    </div>
  );
}
