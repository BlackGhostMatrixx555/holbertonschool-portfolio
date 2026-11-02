import { Outlet, Link } from 'react-router-dom';

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-cream">
      <header className="h-20 px-8 md:px-16 flex items-center justify-between bg-cream border-b border-gray-200">
        <Link to="/" className="flex items-center gap-2 text-2xl font-display font-bold text-navy">
          <span className="w-9 h-8 bg-navy text-white rounded-lg grid place-items-center text-xs">
            {'</>'}
          </span>
          CampOrga
        </Link>
        <Link to="/login" className="text-sm font-semibold text-ink hover:text-coral">
          Espace organisateur ↗
        </Link>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="px-8 md:px-16 py-6 flex items-center justify-between border-t border-gray-200 text-sm text-muted">
        <span className="font-display text-lg text-ink font-bold">CampOrga</span>
        <span>© 2026 — Portfolio Project</span>
      </footer>
    </div>
  );
}
