/**
 * Bulle de chat de la landing page. L'historique est enregistré côté serveur
 * (MongoDB) ; le navigateur garde seulement l'identifiant de session.
 */
// useMutation : gère l'appel réseau d'envoi d'un message, avec états (en cours, succès, erreur).
import { useMutation } from '@tanstack/react-query'
// Hooks React : useEffect (effets de bord), useRef (référence DOM), useState (état local).
// FormEvent : type TypeScript de l'événement d'envoi d'un formulaire.
import { useEffect, useRef, useState, type FormEvent } from 'react'
// Fonction HTTP qui envoie le message au serveur et renvoie la réponse du bot.
import { sendChatMessage } from '../api/endpoints'
// Classe CSS partagée pour les champs de saisie.
import { inputClass } from './ui'

// Une ligne de la conversation : qui parle et le texte.
interface Line {
  role: 'visitor' | 'bot'
  content: string
}

// Questions proposées au visiteur quand la conversation n'a pas encore commencé.
const SUGGESTIONS = ['Quand commence le camp ?', 'Où se passe-t-il ?', 'Reste-t-il des places ?']

export function ChatWidget({ slug, campName }: { slug: string; campName: string }) {
  // Clé de stockage propre à chaque camp, pour que deux camps n'partagent pas de session.
  const storageKey = `camporga.chat.${slug}`
  // Panneau ouvert ou fermé.
  const [open, setOpen] = useState(false)
  // Texte en cours de saisie dans le champ.
  const [draft, setDraft] = useState('')
  // Historique affiché. Le premier message du bot est un message d'accueil local.
  const [lines, setLines] = useState<Line[]>([
    { role: 'bot', content: `Bonjour ! Une question sur « ${campName} » ? Je vous réponds tout de suite.` },
  ])
  // Identifiant de session. La valeur initiale est lue dans sessionStorage, avec une fonction
  // d'initialisation : elle n'est exécutée qu'au premier rendu.
  const [sessionId, setSessionId] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(storageKey)
    } catch {
      // Stockage indisponible (navigation privée stricte, par exemple) : pas de session reprise.
      return null
    }
  })
  // Références DOM : marqueur de fin de conversation et champ de saisie.
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Mutation d'envoi. mutationFn fait l'appel réseau ; onSuccess et onError traitent la réponse.
  const mutation = useMutation({
    mutationFn: (message: string) => sendChatMessage(slug, message, sessionId),
    onSuccess: (data) => {
      // Ajoute la réponse du bot en gardant les lignes précédentes.
      setLines((current) => [...current, { role: 'bot', content: data.reply }])
      // Mémorise l'identifiant de session renvoyé par le serveur pour les messages suivants.
      setSessionId(data.session_id)
      try {
        sessionStorage.setItem(storageKey, data.session_id)
      } catch {
        /* sans stockage, la conversation continue dans cet onglet uniquement */
      }
    },
    // Affiche le message d'erreur comme une réponse du bot.
    onError: (error) => setLines((current) => [...current, { role: 'bot', content: error.message }]),
  })

  // Fait défiler jusqu'au dernier message et place le curseur dans le champ.
  // Se déclenche à l'ouverture du panneau et à chaque nouveau message (lines.length).
  useEffect(() => {
    if (open) {
      // Le « ?. » évite une erreur dans les environnements sans scrollIntoView (tests jsdom notamment).
      endRef.current?.scrollIntoView?.({ block: 'end' })
      inputRef.current?.focus()
    }
  }, [open, lines.length])

  // Envoie un message : ajoute la ligne du visiteur, vide le champ, lance la requête.
  function send(message: string) {
    const text = message.trim()
    // Ignore les messages vides et les envois pendant qu'une réponse est en attente.
    if (!text || mutation.isPending) return
    setLines((current) => [...current, { role: 'visitor', content: text }])
    setDraft('')
    mutation.mutate(text)
  }

  // Soumission du formulaire (Entrée ou bouton Envoyer).
  function onSubmit(event: FormEvent) {
    // Empêche le rechargement de la page, comportement par défaut d'un formulaire HTML.
    event.preventDefault()
    send(draft)
  }

  return (
    // Position fixe en bas à droite, au-dessus du contenu de la page (z-40).
    <div className="fixed bottom-4 right-4 z-40 flex flex-col items-end gap-3">
      {open && (
        <section
          id="chat-panel"
          aria-label="Assistant du camp"
          className="flex h-[28rem] w-[min(22rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-navy-100"
        >
          <header className="flex items-center justify-between bg-navy-900 px-4 py-3 text-white">
            <p className="font-display font-semibold">Assistant CampOrga</p>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg px-2 py-1 text-sm hover:bg-white/10">
              Fermer
            </button>
          </header>
          {/* aria-live : les nouvelles réponses sont annoncées par les lecteurs d'écran */}
          <div className="flex-1 space-y-2 overflow-y-auto p-4" aria-live="polite">
            {lines.map((line, index) => (
              // L'index sert de clé ; acceptable ici car la liste n'est ni réordonnée ni filtrée.
              <p
                key={index}
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                  // Messages du visiteur alignés à droite et en coral, ceux du bot à gauche et en sable.
                  line.role === 'visitor' ? 'ml-auto bg-coral-600 text-white' : 'bg-sand-100 text-navy-900'
                }`}
              >
                {/* sr-only : préfixe lu par les lecteurs d'écran, invisible à l'écran. */}
                <span className="sr-only">{line.role === 'visitor' ? 'Vous : ' : 'Assistant : '}</span>
                {line.content}
              </p>
            ))}
            {mutation.isPending && <p className="text-xs text-navy-500">L'assistant écrit…</p>}
            {/* Élément vide servant de cible au défilement automatique. */}
            <div ref={endRef} />
          </div>
          {/* Suggestions affichées seulement avant le premier message du visiteur. */}
          {lines.length === 1 && (
            <div className="flex flex-wrap gap-2 px-4 pb-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => send(suggestion)}
                  className="rounded-full bg-navy-50 px-3 py-1 text-xs font-medium text-navy-700 hover:bg-navy-100"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={onSubmit} className="flex gap-2 border-t border-navy-100 p-3">
            {/* Libellé masqué visuellement mais lu par les lecteurs d'écran, lié au champ par htmlFor/id. */}
            <label htmlFor="chat-input" className="sr-only">
              Votre question
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              // Limite de longueur côté navigateur, à doubler côté serveur.
              maxLength={500}
              placeholder="Votre question…"
              className={inputClass}
            />
            <button
              type="submit"
              // Désactivé si le champ est vide ou si une réponse est en attente.
              disabled={!draft.trim() || mutation.isPending}
              className="rounded-xl bg-coral-600 px-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              Envoyer
            </button>
          </form>
        </section>
      )}
      {/* Bouton flottant d'ouverture/fermeture. */}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        // Annonce l'état ouvert/fermé et relie le bouton au panneau qu'il contrôle.
        aria-expanded={open}
        aria-controls="chat-panel"
        className="flex h-14 w-14 items-center justify-center rounded-full bg-navy-900 text-white shadow-lg hover:bg-navy-700"
      >
        <span className="sr-only">{open ? "Fermer l'assistant" : "Poser une question à l'assistant"}</span>
        {/* Icône de bulle de dialogue, décorative : le texte sr-only porte le sens. */}
        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  )
}