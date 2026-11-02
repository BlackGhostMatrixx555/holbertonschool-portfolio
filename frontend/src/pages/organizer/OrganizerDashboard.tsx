import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Camp } from '../../types';

export function OrganizerDashboard() {
  const [camps, setCamps] = useState<Camp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/camps')
      .then((res) => setCamps(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-display text-ink mb-6">Mes camps</h1>
      {loading && <p>Chargement…</p>}
      {!loading && camps.length === 0 && <p className="text-muted">Aucun camp pour le moment.</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {camps.map((camp) => (
          <div key={camp.id} className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="text-lg font-semibold text-ink">{camp.name}</h3>
            <p className="text-sm text-muted">{camp.start_date} — {camp.end_date}</p>
            <p className="text-sm text-navy mt-2">{camp.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
