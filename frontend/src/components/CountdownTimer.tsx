/**
 * Compte à rebours jusqu'au début du camp, mis à jour chaque seconde.
 * aria-live="off" : un lecteur d'écran ne doit pas annoncer chaque seconde.
 */
import { useEffect, useState } from 'react'
import type { SeasonTheme } from '../api/types'
import { countdownTo, seasonStyles } from '../lib/season'

export function CountdownTimer({ startDate, season }: { startDate: string; season: SeasonTheme }) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(timer) // nettoyage quand le composant disparaît
  }, [])

  const remaining = countdownTo(startDate, now)
  const style = seasonStyles[season]

  if (remaining.started) {
    return <p className="font-display text-lg font-semibold">Le camp a commencé, à bientôt pour la prochaine édition !</p>
  }

  const units = [
    { value: remaining.days, label: 'jours' },
    { value: remaining.hours, label: 'heures' },
    { value: remaining.minutes, label: 'minutes' },
    { value: remaining.seconds, label: 'secondes' },
  ]

  return (
    <div role="timer" aria-live="off" aria-label={`Début dans ${remaining.days} jours`}>
      <p className="mb-2 text-sm font-medium text-navy-700">Début du camp dans</p>
      <dl className="grid grid-cols-4 gap-2 sm:gap-3">
        {units.map((unit) => (
          // flex-col-reverse : le chiffre s'affiche au-dessus, mais <dt> reste avant <dd> (HTML valide)
          <div key={unit.label} className={`flex flex-col-reverse rounded-2xl ${style.soft} px-2 py-3 text-center`}>
            <dt className="text-xs font-medium text-navy-700">{unit.label}</dt>
            <dd className="font-display text-2xl font-bold tabular-nums sm:text-4xl">{String(unit.value).padStart(2, '0')}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
