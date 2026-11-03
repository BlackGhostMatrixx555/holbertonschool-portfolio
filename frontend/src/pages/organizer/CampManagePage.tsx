/** Gestion d'un camp : inscriptions, landing page, messages et chatbot, en onglets. */
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import {
  fetchCamp,
  fetchChatStats,
  fetchConversations,
  fetchMessages,
  fetchRegistrations,
  saveLandingPage,
  setAttendance,
  setMessageStatus,
} from '../../api/endpoints'
import type { Camp, MessageStatus } from '../../api/types'
import { Tabs } from '../../components/Tabs'
import { Alert, Button, Card, EmptyState, Field, inputClass, LinkButton, PageHeader, Spinner, StatusBadge } from '../../components/ui'
import { formatDateTime, formatRange, intentLabels, messageStatusLabels, seasonLabels } from '../../lib/format'
import { seasonFromDate } from '../../lib/season'

// ---- Onglet Inscriptions -------------------------------------------------------

function RegistrationsTab({ camp }: { camp: Camp }) {
  const queryClient = useQueryClient()
  const registrations = useQuery({
    queryKey: ['registrations', camp.id],
    queryFn: () => fetchRegistrations(camp.id),
    staleTime: 0, // toujours recharger : de nouvelles inscriptions arrivent à tout moment
  })
  // Affichage optimiste : pendant l'enregistrement, la case montre déjà la nouvelle
  // valeur (attendance.variables). Si l'API refuse, elle revient à la valeur du serveur.
  // onSettled renvoie une promesse : la mutation reste "en cours" jusqu'au rechargement
  // de la liste, ce qui évite tout clignotement.
  const attendance = useMutation({
    mutationFn: ({ id, confirmed }: { id: string; confirmed: boolean }) => setAttendance(id, confirmed),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['registrations', camp.id] }),
  })
  const pending = attendance.isPending ? attendance.variables : undefined

  if (registrations.isPending) return <Spinner />
  if (registrations.isError) return <Alert>{registrations.error.message}</Alert>
  if (registrations.data.length === 0) {
    return <EmptyState title="Aucun inscrit pour l'instant">Publiez la landing page et partagez son lien.</EmptyState>
  }

  const confirmed = registrations.data.filter((registration) => registration.confirmed).length

  return (
    <Card>
      <p className="mb-4 text-sm text-navy-500">
        {registrations.data.length} inscrit(s) sur {camp.capacity} places · {confirmed} présence(s) confirmée(s)
      </p>
      {attendance.error && <Alert>{attendance.error.message}</Alert>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <caption className="sr-only">Liste des inscrits au camp {camp.name}</caption>
          <thead className="border-b border-navy-100 text-navy-500">
            <tr>
              <th scope="col" className="py-2 pr-4 font-medium">Participant</th>
              <th scope="col" className="py-2 pr-4 font-medium">Email</th>
              <th scope="col" className="py-2 pr-4 font-medium">Commentaire</th>
              <th scope="col" className="py-2 pr-4 font-medium">Inscrit le</th>
              <th scope="col" className="py-2 font-medium">Présence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-100">
            {registrations.data.map((registration) => (
              <tr key={registration.id}>
                <td className="py-3 pr-4 font-medium">
                  {registration.first_name} {registration.last_name}
                </td>
                <td className="py-3 pr-4">
                  <a href={`mailto:${registration.email}`} className="text-navy-700 hover:underline">
                    {registration.email}
                  </a>
                </td>
                <td className="max-w-[14rem] py-3 pr-4 text-navy-500">{registration.comment || '–'}</td>
                <td className="py-3 pr-4 text-navy-500">{formatDateTime(registration.created_at)}</td>
                <td className="py-3">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={pending?.id === registration.id ? pending.confirmed : registration.confirmed}
                      onChange={(event) => attendance.mutate({ id: registration.id, confirmed: event.target.checked })}
                      className="h-5 w-5 accent-coral-600"
                    />
                    <span className="sr-only">
                      Présence confirmée pour {registration.first_name} {registration.last_name}
                    </span>
                    <span aria-hidden="true">{registration.confirmed ? 'Confirmée' : 'À confirmer'}</span>
                  </label>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

// ---- Onglet Landing page -------------------------------------------------------

const landingSchema = z.object({
  season_theme: z.enum(['spring', 'summer', 'autumn', 'winter']),
  hero_title: z.string().trim().min(1, 'Le titre est obligatoire.').max(200),
  hero_description: z.string().max(2000, '2000 caractères maximum.'),
})
type LandingValues = z.infer<typeof landingSchema>

function LandingTab({ camp }: { camp: Camp }) {
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LandingValues>({
    resolver: zodResolver(landingSchema),
    defaultValues: {
      season_theme: camp.landing_page?.season_theme ?? seasonFromDate(camp.start_date),
      hero_title: camp.landing_page?.hero_title ?? camp.name,
      hero_description: camp.landing_page?.hero_description ?? '',
    },
  })

  const save = useMutation({
    mutationFn: ({ values, publish }: { values: LandingValues; publish: boolean }) =>
      saveLandingPage(camp.id, { ...values, hero_description: values.hero_description.trim() || null, publish }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['camp', camp.id] })
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['public-camps'] })
    },
  })

  const published = camp.status === 'published'

  return (
    <Card>
      <form noValidate className="space-y-4">
        <Field label="Thème saisonnier" hint="Change les couleurs et le style du compte à rebours.">
          {(props) => (
            <select {...props} {...register('season_theme')} className={`${inputClass} sm:max-w-xs`}>
              {Object.entries(seasonLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Titre d'accroche" required error={errors.hero_title?.message}>
          {(props) => <input {...props} {...register('hero_title')} className={inputClass} />}
        </Field>
        <Field label="Texte d'accroche" error={errors.hero_description?.message}>
          {(props) => <textarea {...props} {...register('hero_description')} rows={3} className={inputClass} />}
        </Field>

        {save.isSuccess && (
          <Alert tone="success">
            {save.variables?.publish ? 'Landing page publiée : les inscriptions sont ouvertes.' : 'Landing page enregistrée en brouillon.'}
          </Alert>
        )}
        {save.error && <Alert>{save.error.message}</Alert>}

        <div className="flex flex-wrap gap-3">
          <Button type="button" disabled={save.isPending} onClick={handleSubmit((values) => save.mutate({ values, publish: true }))}>
            {published ? 'Mettre à jour (en ligne)' : 'Publier'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={save.isPending}
            onClick={handleSubmit((values) => save.mutate({ values, publish: false }))}
          >
            {published ? 'Dépublier (brouillon)' : 'Enregistrer en brouillon'}
          </Button>
        </div>
      </form>
    </Card>
  )
}

// ---- Onglet Messages -------------------------------------------------------------

function MessagesTab({ camp }: { camp: Camp }) {
  const queryClient = useQueryClient()
  const messages = useQuery({ queryKey: ['messages', camp.id], queryFn: () => fetchMessages(camp.id), staleTime: 0 })
  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: MessageStatus }) => setMessageStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['messages', camp.id] }),
  })

  if (messages.isPending) return <Spinner />
  if (messages.isError) return <Alert>{messages.error.message}</Alert>
  if (messages.data.length === 0) return <EmptyState title="Aucun message reçu" />

  return (
    <ul className="space-y-3">
      {messages.data.map((message) => (
        <li key={message.id}>
          <Card className={message.status === 'unread' ? 'ring-coral-400' : ''}>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-semibold">
                  {message.name}{' '}
                  <a href={`mailto:${message.email}`} className="font-normal text-navy-500 hover:underline">
                    {message.email}
                  </a>
                </p>
                <p className="text-xs text-navy-500">{formatDateTime(message.created_at)}</p>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <span className="text-navy-500">Statut</span>
                <select
                  value={message.status}
                  onChange={(event) => updateStatus.mutate({ id: message.id, status: event.target.value as MessageStatus })}
                  className="rounded-lg border border-navy-100 bg-white px-2 py-1 text-sm"
                >
                  {Object.entries(messageStatusLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="mt-3 whitespace-pre-line text-sm">{message.message}</p>
          </Card>
        </li>
      ))}
    </ul>
  )
}

// ---- Onglet Chatbot (données MongoDB) -----------------------------------------

function ChatTab({ camp }: { camp: Camp }) {
  const stats = useQuery({ queryKey: ['chat-stats', camp.id], queryFn: () => fetchChatStats(camp.id), staleTime: 0 })
  const conversations = useQuery({
    queryKey: ['conversations', camp.id],
    queryFn: () => fetchConversations(camp.id),
    staleTime: 0,
  })

  if (stats.isPending) return <Spinner />
  if (stats.isError) return <Alert>{stats.error.message}</Alert>

  const max = Math.max(1, ...stats.data.top_intents.map((item) => item.count))

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
      <Card>
        <h2 className="text-lg font-bold">Questions les plus posées</h2>
        <p className="mt-1 text-sm text-navy-500">
          {stats.data.conversations} conversation(s) · {stats.data.visitor_messages} question(s)
        </p>
        {stats.data.top_intents.length === 0 ? (
          <p className="mt-4 text-sm text-navy-500">Pas encore de question.</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {stats.data.top_intents.map((item) => (
              <li key={item.intent}>
                <div className="flex justify-between text-sm">
                  <span>{intentLabels[item.intent] ?? item.intent}</span>
                  <span className="font-semibold tabular-nums">{item.count}</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-navy-50" aria-hidden="true">
                  <div className="h-2 rounded-full bg-coral-400" style={{ width: `${(item.count / max) * 100}%` }} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card>
        <h2 className="text-lg font-bold">Dernières conversations</h2>
        {conversations.isPending && <Spinner />}
        {conversations.data?.length === 0 && <p className="mt-4 text-sm text-navy-500">Aucune conversation.</p>}
        <ul className="mt-4 space-y-4">
          {conversations.data?.map((conversation) => (
            <li key={conversation.session_id} className="rounded-xl bg-sand-50 p-3">
              <p className="text-xs text-navy-500">{formatDateTime(conversation.updated_at)}</p>
              <ul className="mt-2 space-y-1 text-sm">
                {conversation.messages
                  .filter((message) => message.role === 'visitor')
                  .map((message, index) => (
                    <li key={index}>
                      « {message.content} »{' '}
                      <span className="text-xs text-navy-500">({intentLabels[message.intent ?? ''] ?? message.intent})</span>
                    </li>
                  ))}
              </ul>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}

// ---- Page ----------------------------------------------------------------------

export function CampManagePage() {
  const { campId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('onglet') ?? 'inscriptions' // l'onglet est dans l'URL : partageable
  const camp = useQuery({ queryKey: ['camp', campId], queryFn: () => fetchCamp(campId), staleTime: 0 })

  useEffect(() => {
    if (camp.data) document.title = `${camp.data.name} – Espace CampOrga`
  }, [camp.data])

  if (camp.isPending) return <Spinner />
  if (camp.isError) return <Alert>{camp.error.message}</Alert>

  const data = camp.data
  return (
    <>
      <PageHeader
        title={data.name}
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            <StatusBadge status={data.status} />
            {data.city} · {formatRange(data.start_date, data.end_date)} · {data.registrations_count}/{data.capacity} inscrits
          </span>
        }
        actions={
          <>
            {data.status === 'published' && (
              <LinkButton to={`/camps/${data.slug}`} variant="secondary" target="_blank" rel="noopener noreferrer">
                Voir la page publique<span className="sr-only"> (nouvelle fenêtre)</span>
              </LinkButton>
            )}
            <LinkButton to={`/espace/camps/${data.id}/modifier`} variant="secondary">
              Modifier
            </LinkButton>
          </>
        }
      />
      <p className="-mt-3 mb-6 text-sm">
        <Link to="/espace" className="text-navy-500 hover:underline">
          ← Retour au tableau de bord
        </Link>
      </p>
      <Tabs
        active={tab}
        onChange={(id) => setSearchParams({ onglet: id }, { replace: true })}
        items={[
          { id: 'inscriptions', label: 'Inscriptions', content: <RegistrationsTab camp={data} /> },
          { id: 'landing', label: 'Landing page', content: <LandingTab camp={data} /> },
          { id: 'messages', label: 'Messages', content: <MessagesTab camp={data} /> },
          { id: 'chatbot', label: 'Chatbot', content: <ChatTab camp={data} /> },
        ]}
      />
    </>
  )
}
