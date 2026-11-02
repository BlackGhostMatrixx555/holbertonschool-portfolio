import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Camp } from '../../types';

export function LandingPage() {
  const [camps, setCamps] = useState<Camp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/camps')
      .then((res) => setCamps(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Hero */}
      <section className="bg-[#EAF1E8] py-20 px-8 md:px-24">
        <div className="max-w-2xl">
          <p className="text-navy font-bold tracking-widest text-xs mb-4">
            APPRENDRE · CRÉER · PARTAGER
          </p>
          <h1 className="text-5xl md:text-7xl text-ink leading-tight mb-6">
            Le code ouvre de nouveaux horizons.
          </h1>
          <p className="text-lg text-ink/70 mb-8">
            Découvrez des camps pour explorer l'informatique, apprendre en équipe et créer vos premiers projets.
          </p>
          <a href="#camps" className="inline-flex items-center gap-2 bg-coral text-white px-6 py-3 rounded-lg font-semibold hover:bg-coral-dark transition-colors">
            Découvrir les camps →
          </a>
        </div>
      </section>

      {/* Camps */}
      <section id="camps" className="py-20 px-8 md:px-24">
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-navy font-bold tracking-widest text-xs mb-2">LE PROGRAMME</p>
            <h2 className="text-4xl text-ink">Les prochains camps</h2>
          </div>
          {!loading && <span className="text-muted text-sm">{camps.length} camp(s)</span>}
        </div>

        {loading && <p className="text-muted">Chargement des camps…</p>}
        {!loading && camps.length === 0 && <p className="text-muted">Aucun camp public pour le moment.</p>}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {camps.map((camp) => (
            <article key={camp.id} className="bg-white rounded-2xl overflow-hidden border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="h-32 bg-gradient-to-br from-navy-light to-navy grid place-items-center text-white text-4xl font-bold">
                {'</>'}
              </div>
              <div className="p-6">
                <p className="text-coral text-xs font-bold mb-2">{camp.city || 'Lieu à confirmer'}</p>
                <h3 className="text-xl text-ink mb-2">{camp.name}</h3>
                <p className="text-muted text-sm mb-4">{camp.description || 'Découvrez le programme.'}</p>
                <p className="text-ink text-sm">{camp.start_date} — {camp.end_date}</p>
                {camp.price > 0 && (
                  <p className="text-navy font-bold text-sm mt-2">{camp.price / 100} €</p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
