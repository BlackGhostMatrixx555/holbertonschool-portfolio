/**
 * Onglets accessibles (modèle WAI-ARIA "Tabs") :
 * flèches gauche/droite pour changer d'onglet, rôles tablist/tab/tabpanel.
 */
// useId : génère un identifiant unique stable, utile pour relier les onglets à leurs panneaux.
// useRef : conserve les références aux boutons d'onglets sans déclencher de rendu.
// KeyboardEvent, ReactNode : types TypeScript (événement clavier, contenu React).
import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react'

// Structure d'un onglet : identifiant, libellé affiché et contenu du panneau.
export interface TabItem {
  id: string
  label: string
  content: ReactNode
}

// items : liste des onglets. active : identifiant de l'onglet sélectionné. onChange : appelé au changement.
export function Tabs({ items, active, onChange }: { items: TabItem[]; active: string; onChange: (id: string) => void }) {
  // baseId : préfixe unique pour éviter les conflits d'identifiants si plusieurs Tabs sont présents.
  const baseId = useId()
  // Tableau des boutons, indexé par position, pour pouvoir leur donner le focus au clavier.
  const refs = useRef<Array<HTMLButtonElement | null>>([])

  // Gestion des flèches : ArrowRight avance, ArrowLeft recule, avec retour circulaire.
  function onKeyDown(event: KeyboardEvent, index: number) {
    // Calcule le décalage : +1, -1, ou 0 pour les autres touches.
    const offset = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    // Pour les autres touches, on ne fait rien et on laisse le comportement par défaut.
    if (!offset) return
    // Empêche le défilement de la page par les flèches.
    event.preventDefault()
    // Modulo : + items.length évite un indice négatif, % boucle en fin de liste.
    const next = (index + offset + items.length) % items.length
    onChange(items[next].id)
    // Déplace le focus sur le nouvel onglet, comme le veut le modèle WAI-ARIA.
    refs.current[next]?.focus()
  }

  return (
    <div>
      {/* role="tablist" : conteneur des onglets pour les technologies d'assistance. aria-label le nomme. */}
      {/* overflow-x-auto : défilement horizontal sur petit écran plutôt que casse de la mise en page. */}
      <div role="tablist" aria-label="Gestion du camp" className="flex gap-1 overflow-x-auto border-b border-navy-100">
        {items.map((item, index) => {
          const selected = item.id === active
          return (
            <button
              key={item.id}
              // Callback ref : range le bouton à sa position dans le tableau. Les accolades évitent de renvoyer la valeur.
              ref={(element) => {
                refs.current[index] = element
              }}
              role="tab"
              type="button"
              // Identifiant unique reliant l'onglet à son panneau (via aria-labelledby et aria-controls).
              id={`${baseId}-tab-${item.id}`}
              // Indique à l'utilisateur de lecteur d'écran quel onglet est actif.
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${item.id}`}
              // Roving tabindex : seul l'onglet actif est dans l'ordre de tabulation. Les flèches parcourent les autres.
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(item.id)}
              onKeyDown={(event) => onKeyDown(event, index)}
              className={`whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-semibold transition ${
                selected ? 'border-coral-600 text-navy-900' : 'border-transparent text-navy-500 hover:text-navy-900'
              }`}
            >
              {item.label}
            </button>
          )
        })}
      </div>
      {/* Un panneau par onglet. Tous sont dans le DOM, sauf le contenu, rendu seulement pour l'onglet actif. */}
      {items.map((item) => (
        <div
          key={item.id}
          role="tabpanel"
          id={`${baseId}-panel-${item.id}`}
          // Nomme le panneau par son onglet, pour les lecteurs d'écran.
          aria-labelledby={`${baseId}-tab-${item.id}`}
          // hidden retire les panneaux inactifs de l'affichage et de l'arbre d'accessibilité.
          hidden={item.id !== active}
          className="pt-6"
        >
          {/* Le contenu n'est monté que pour l'onglet actif : les composants inactifs ne lancent pas leurs requêtes. */}
          {item.id === active && item.content}
        </div>
      ))}
    </div>
  )
}