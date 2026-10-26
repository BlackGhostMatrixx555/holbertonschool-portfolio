import { useEffect, useState } from 'react'
import './App.css'

type Camp = {
  id?: string
  slug?: string
  name?: string
  description?: string
  city?: string
  start_date?: string
  end_date?: string
}

function App() {
  const [camps, setCamps] = useState<Camp[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCamps() {
      try {
        const response = await fetch('http://localhost:8000/api/public/camps')
        if (!response.ok) throw new Error('Erreur lors du chargement des camps')

        const data: unknown = await response.json()
        if (Array.isArray(data)) {
          setCamps(data)
        } else if (
          typeof data === 'object' &&
          data !== null &&
          'camps' in data &&
          Array.isArray(data.camps)
        ) {
          setCamps(data.camps)
        } else {
          setCamps([])
        }
      } catch {
        setError('Impossible de joindre le backend. Vérifiez qu’il est démarré.')
      } finally {
        setLoading(false)
      }
    }

    void loadCamps()
  }, [])

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/">CampOrga</a>
        <a className="organizer-link" href="http://localhost:8000/docs">
          Espace organisateur ↗
        </a>
      </header>

      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">APPRENDRE · CRÉER · PARTAGER</p>
          <h1>Le code ouvre de nouveaux horizons.</h1>
          <p className="hero-copy">
            Découvrez des camps pour explorer l’informatique, apprendre en équipe
            et créer vos premiers projets.
          </p>
          <a className="primary-button" href="#camps">Découvrir les camps ↓</a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <span className="code-card">&lt;/&gt;</span>
        </div>
      </section>

      <section className="camps-section" id="camps">
        <div className="section-heading">
          <div>
            <p className="eyebrow">LE PROGRAMME</p>
            <h2>Les prochains camps</h2>
          </div>
          {!loading && <span className="camp-count">{camps.length} camp(s)</span>}
        </div>

        {loading && <p className="notice">Chargement des camps…</p>}
        {error && <p className="notice error">{error}</p>}
        {!loading && !error && camps.length === 0 && (
          <p className="notice">Aucun camp public pour le moment.</p>
        )}

        <div className="camp-grid">
          {camps.map((camp, index) => (
            <article className="camp-card" key={camp.id ?? camp.slug ?? index}>
              <div className={`camp-illustration illustration-${index % 3}`}>
                <span className="illustration-symbol" aria-hidden="true">{'{ }'}</span>
                <span className="camp-label">SUMMER CAMP</span>
              </div>
              <div className="camp-info">
                <p className="camp-location">{camp.city ?? 'Lieu à confirmer'}</p>
                <h3>{camp.name ?? 'Summer camp'}</h3>
                <p className="camp-description">
                  {camp.description ?? 'Découvrez le programme de ce camp.'}
                </p>
                <p className="camp-dates">
                  {camp.start_date ?? 'Date à confirmer'} — {camp.end_date ?? 'Date à confirmer'}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}

export default App