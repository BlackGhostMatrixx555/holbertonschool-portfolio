/**
 * Bulle de chat de la landing page. L'historique est enregistré côté serveur
 * (MongoDB) ; le navigateur garde seulement l'identifiant de session.
 */
import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { sendChatMessage } from '../api/endpoints'
import { inputClass } from './ui'

interface Line {
  role: 'visitor' | 'bot'
  content: string
}

const SUGGESTIONS = ['Quand commence le camp ?', 'Où se passe-t-il ?', 'Reste-t-il des places ?']

export function ChatWidget({ slug, campName }: { slug: string; campName: string }) {
  const storageKey = `camporga.chat.${slug}`
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [lines, setLines] = useState<Line[]>([
    { role: 'bot', content: `Bonjour ! Une question sur « ${campName} » ? Je vous réponds tout de suite.` },
  ])
  const [sessionId, setSessionId] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(storageKey)
    } catch {
      return null
    }
  })
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const mutation = useMutation({
    mutationFn: (message: string) => sendChatMessage(slug, message, sessionId),
    onSuccess: (data) => {
      setLines((current) => [...current, { role: 'bot', content: data.reply }])
      setSessionId(data.session_id)
      try {
        sessionStorage.setItem(storageKey, data.session_id)
      } catch {
        /* sans stockage, la conversation continue dans cet onglet uniquement */
      }
    },
    onError: (error) => setLines((current) => [...current, { role: 'bot', content: error.message }]),
  })

  // Fait défiler jusqu'au dernier message et place le curseur dans le champ.
  useEffect(() => {
    if (open) {
      endRef.current?.scrollIntoView?.({ block: 'end' })
      inputRef.current?.focus()
    }
  }, [open, lines.length])

  function send(message: string) {
    const text = message.trim()
    if (!text || mutation.isPending) return
    setLines((current) => [...current, { role: 'visitor', content: text }])
    setDraft('')
    mutation.mutate(text)
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    send(draft)
  }

  return (
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
              <p
                key={index}
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                  line.role === 'visitor' ? 'ml-auto bg-coral-600 text-white' : 'bg-sand-100 text-navy-900'
                }`}
              >
                <span className="sr-only">{line.role === 'visitor' ? 'Vous : ' : 'Assistant : '}</span>
                {line.content}
              </p>
            ))}
            {mutation.isPending && <p className="text-xs text-navy-500">L'assistant écrit…</p>}
            <div ref={endRef} />
          </div>
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
            <label htmlFor="chat-input" className="sr-only">
              Votre question
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              maxLength={500}
              placeholder="Votre question…"
              className={inputClass}
            />
            <button
              type="submit"
              disabled={!draft.trim() || mutation.isPending}
              className="rounded-xl bg-coral-600 px-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              Envoyer
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="chat-panel"
        className="flex h-14 w-14 items-center justify-center rounded-full bg-navy-900 text-white shadow-lg hover:bg-navy-700"
      >
        <span className="sr-only">{open ? "Fermer l'assistant" : "Poser une question à l'assistant"}</span>
        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  )
}
