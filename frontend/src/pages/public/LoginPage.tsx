import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/admin');
    } catch {
      setError('Email ou mot de passe incorrect.');
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-surface p-8">
      <form onSubmit={handleSubmit} className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
        <h1 className="text-3xl text-ink mb-2">Connexion</h1>
        <p className="text-muted text-sm mb-6">Accédez à votre espace organisateur.</p>
        {error && <p className="text-coral text-sm mb-4">{error}</p>}
        <div className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          />
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          />
        </div>
        <button type="submit" className="w-full mt-6 bg-coral text-white py-3 rounded-lg font-semibold hover:bg-coral-dark">
          Se connecter
        </button>
        <p className="text-sm text-muted mt-4 text-center">
          Pas de compte ?{' '}
          <Link to="/register" className="text-navy font-semibold">
            S'inscrire
          </Link>
        </p>
      </form>
    </div>
  );
}
