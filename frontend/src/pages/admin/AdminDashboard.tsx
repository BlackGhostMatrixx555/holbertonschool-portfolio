import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { User } from '../../types';

export function AdminDashboard() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    api.get('/users')
      .then((res) => setUsers(res.data))
      .catch(() => {});
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-display mb-6">Tableau de bord Admin</h1>
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h2 className="text-xl font-display mb-4">Utilisateurs ({users.length})</h2>
        <table className="w-full text-left">
          <thead className="border-b border-gray-200">
            <tr>
              <th className="py-2">Email</th>
              <th>Rôle</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-gray-100">
                <td className="py-2">{u.email}</td>
                <td>{u.role}</td>
                <td>{u.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
