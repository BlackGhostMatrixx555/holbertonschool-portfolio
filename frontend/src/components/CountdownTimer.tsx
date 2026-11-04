/**
 * Compte à rebours jusqu'au début du camp, mis à jour chaque seconde.
 * aria-live="off" : un lecteur d'écran ne doit pas annoncer chaque seconde.
 */
// useEffect : effets de bord (ici, le minuteur). useState : état local de la date courante.
import { useEffect, useState } from 'react'
// Type du thème de saison (ex. 'spring', 'summer').
import type { SeasonTheme } from '../api/types'
// countdownTo : calcule jours, heures, minutes, secondes restants. seasonStyles : classes CSS par saison.
import { countdownTo, seasonStyles } from '../lib/season'

export function CountdownTimer({ startDate, season }: { startDate: string; season: SeasonTheme }) {
  // Date courante, initialisée une seule fois au premier rendu grâce à la fonction passée à useState.
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    // Met à jour la date toutes les 1000 ms, donc le compte à rebours avance chaque seconde.
    const timer = window.setInterval(() => setNow(new Date()), 1000)
    // Fonction de nettoyage : arrête le minuteur quand le composant est retiré de l'écran,
    // pour éviter les fuites mémoire et les mises à jour sur un composant disparu.
    return () => window.clearInterval(timer)
  }, [])

  // Calcule le temps restant à partir de la date courante. Recalculé à chaque rendu.
  const remaining = countdownTo(startDate, now)
  const style = seasonStyles[season]

  // Le camp a déjà commencé : on affiche un message à la place du compte à rebours.
  if (remaining.started) {
    return <p className="font-display text-lg font-semibold">Le camp a commencé, à bientôt pour la prochaine édition !</p>
  }

  // Tableau des unités à afficher, pour éviter de répéter le même bloc JSX quatre fois.
  const units = [
    { value: remaining.days, label: 'jours' },
    { value: remaining.hours, label: 'heures' },
    { value: remaining.minutes, label: 'minutes' },
    { value: remaining.seconds, label: 'secondes' },
  ]

  return (
    // role="timer" : rôle ARIA pour un minuteur. aria-live="off" : pas d'annonce automatique.
    // aria-label donne un nom accessible global, ici uniquement le nombre de jours.
    <div role="timer" aria-live="off" aria-label={`Début dans ${remaining.days} jours`}>
      <p className="mb-2 text-sm font-medium text-navy-700">Début du camp dans</p>
      <dl className="grid grid-cols-4 gap-2 sm:gap-3">
        {units.map((unit) => (
          // flex-col-reverse : inverse l'ordre visuel, donc le chiffre (dd) s'affiche au-dessus du libellé (dt).
          // Le DOM garde dt avant dd, ce qui reste conforme à la structure HTML d'une liste de descriptions.
          // tabular-nums : chiffres de largeur fixe, pour éviter que le texte ne bouge à chaque seconde.
          <div key={unit.label} className={`flex flex-col-reverse rounded-2xl ${style.soft} px-2 py-3 text-center`}>
            <dt className="text-xs font-medium text-navy-700">{unit.label}</dt>
            {/* padStart(2, '0') : ajoute un zéro devant les valeurs à un chiffre (ex. 05). */}
            <dd className="font-display text-2xl font-bold tabular-nums sm:text-4xl">{String(unit.value).padStart(2, '0')}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}