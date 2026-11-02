import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function RegisterPage() {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await register(form);
      navigate('/admin');
    } catch {
      setError("Erreur lors de l'inscription.");
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-surface p-8">
      <form onSubmit={handleSubmit} className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
        <h1 className="text-3xl text-ink mb-2">Créer un compte</h1>
        <p className="text-muted text-sm mb-6">Devenez organisateur de camps.</p>
        {error && <p className="text-coral text-sm mb-4">{error}</p>}
        <div className="space-y-4">
          <input
            placeholder="Prénom"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          />
          <input
            placeholder="Nom"
            value={form.last_name}
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          />
          <input
            type="password"
            placeholder="Mot de passe (8 caractères minimum)"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
            minLength={8}
          />
        </div>
        <button type="submit" className="w-full mt-6 bg-coral text-white py-3 rounded-lg font-semibold hover:bg-coral-dark">
          S'inscrire
        </button>
        <p className="text-sm text-muted mt-4 text-center">
          Déjà un compte ?{' '}
          <Link to="/login" className="text-navy font-semibold">
            Se connecter
          </Link>
        </p>
      </form>
    </div>
  );
}
