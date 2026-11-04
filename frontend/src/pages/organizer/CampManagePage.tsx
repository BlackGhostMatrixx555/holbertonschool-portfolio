/** Gestion d'un camp : inscriptions, landing page, messages et chatbot, en onglets. */

// zodResolver : relie le schéma de validation Zod à react-hook-form.
import { zodResolver } from '@hookform/resolvers/zod'

// useMutation : exécute une écriture (POST, PUT...) avec suivi d'état.
// useQuery : lecture avec cache. useQueryClient : accès au cache pour le recharger ou l'invalider.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// useEffect : effet de bord, ici la mise à jour du titre de l'onglet.
import { useEffect } from 'react'

// useForm : gestion d'un formulaire (valeurs, erreurs, soumission).
import { useForm } from 'react-hook-form'

// Link : lien interne. useParams : lit l'id du camp dans l'URL. useSearchParams : lit et écrit les paramètres de l'URL (?onglet=...).
import { Link, useParams, useSearchParams } from 'react-router-dom'

// z : bibliothèque de validation de schémas.
import { z } from 'zod'

// Fonctions d'appel à l'API, une par donnée ou action.
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

// Types TypeScript : Camp (structure d'un camp) et MessageStatus (valeurs possibles d'un statut de message).
import type { Camp, MessageStatus } from '../../api/types'

// Composant d'onglets, avec un état actif et un contenu par onglet.
import { Tabs } from '../../components/Tabs'

// Composants d'interface partagés.
import { Alert, Button, Card, EmptyState, Field, inputClass, LinkButton, PageHeader, Spinner, StatusBadge } from '../../components/ui'

// Fonctions de mise en forme et libellés traduits.
import { formatDateTime, formatRange, intentLabels, messageStatusLabels, seasonLabels } from '../../lib/format'

// Déduit la saison à partir d'une date (valeur par défaut du thème).
import { seasonFromDate } from '../../lib/season'

// ---- Onglet Inscriptions -------------------------------------------------------

// Reçoit le camp complet en prop. Affiche la liste des inscrits et permet de confirmer la présence.
function RegistrationsTab({ camp }: { camp: Camp }) {
  const queryClient = useQueryClient()

  // Liste des inscrits du camp. staleTime: 0 : rechargement à chaque affichage.
  const registrations = useQuery({
    queryKey: ['registrations', camp.id],
    queryFn: () => fetchRegistrations(camp.id),
    staleTime: 0, // toujours recharger : de nouvelles inscriptions arrivent à tout moment
  })

  // Mutation de présence. Le commentaire décrit l'affichage optimiste, mais le code ne l'implémente pas :
  // la case reflète le serveur via invalidation, donc elle ne change qu'après réponse de l'API.
  // onSettled : appelé après succès ou échec. Renvoyer la promesse de invalidateQueries garde isPending vrai
  // jusqu'au rechargement, ce qui évite un clignotement de la case.
  const attendance = useMutation({
    mutationFn: ({ id, confirmed }: { id: string; confirmed: boolean }) => setAttendance(id, confirmed),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['registrations', camp.id] }),
  })

  // Pendant la mutation, variables contient les arguments envoyés (id et nouvelle valeur).
  // Sert à afficher la nouvelle valeur d'une seule ligne pendant l'attente.
  const pending = attendance.isPending ? attendance.variables : undefined

  if (registrations.isPending) return <Spinner />
  if (registrations.isError) return <Alert>{registrations.error.message}</Alert>

  // Liste vide : message avec un conseil.
  if (registrations.data.length === 0) {
    return <EmptyState title="Aucun inscrit pour l'instant">Publiez la landing page et partagez son lien.</EmptyState>
  }

  // Nombre de présences confirmées, calculé à partir des données reçues.
  const confirmed = registrations.data.filter((registration) => registration.confirmed).length

  return (
    <Card>
      <p className="mb-4 text-sm text-navy-500">
        {registrations.data.length} inscrit(s) sur {camp.capacity} places · {confirmed} présence(s) confirmée(s)
      </p>
      {attendance.error && <Alert>{attendance.error.message}</Alert>}

      {/* overflow-x-auto : défilement horizontal du tableau sur petit écran. min-w évite que les colonnes s'écrasent. */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-sm">
          {/* caption sr-only : titre du tableau pour les lecteurs d'écran, invisible à l'écran. */}
          <caption className="sr-only">Liste des inscrits au camp {camp.name}</caption>
          <thead className="border-b border-navy-100 text-navy-500">
            <tr>
              {/* scope="col" : indique aux lecteurs d'écran que l'en-tête s'applique à la colonne. */}
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
                {/* max-w : limite la largeur du commentaire, qui peut être long. */}
                <td className="max-w-[14rem] py-3 pr-4 text-navy-500">{registration.comment || '–'}</td>
                <td className="py-3 pr-4 text-navy-500">{formatDateTime(registration.created_at)}</td>
                <td className="py-3">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      // Si cette ligne est en cours de mise à jour, on affiche la valeur demandée ;
                      // sinon, la valeur du serveur.
                      checked={pending?.id === registration.id ? pending.confirmed : registration.confirmed}
                      onChange={(event) => attendance.mutate({ id: registration.id, confirmed: event.target.checked })}
                      className="h-5 w-5 accent-coral-600"
                    />
                    {/* Libellé lu par les lecteurs d'écran, masqué visuellement. */}
                    <span className="sr-only">
                      Présence confirmée pour {registration.first_name} {registration.last_name}
                    </span>
                    {/* Texte visible, masqué aux lecteurs d'écran pour éviter une double annonce. */}
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

// Schéma de validation du formulaire de landing page.
const landingSchema = z.object({
  // enum : seules ces quatre valeurs sont acceptées.
  season_theme: z.enum(['spring', 'summer', 'autumn', 'winter']),
  // trim() retire les espaces avant la validation, min(1) refuse donc un titre blanc.
  hero_title: z.string().trim().min(1, 'Le titre est obligatoire.').max(200),
  hero_description: z.string().max(2000, '2000 caractères maximum.'),
})

// Type TypeScript déduit du schéma : évite de le réécrire à la main.
type LandingValues = z.infer<typeof landingSchema>

function LandingTab({ camp }: { camp: Camp }) {
  const queryClient = useQueryClient()

  // Initialisation du formulaire : résolveur Zod, valeurs par défaut issues du camp existant
  // (ou valeurs de repli : saison déduite de la date, nom du camp comme titre).
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

  // Enregistrement de la landing page. publish indique s'il faut la mettre en ligne ou la garder en brouillon.
  const save = useMutation({
    mutationFn: ({ values, publish }: { values: LandingValues; publish: boolean }) =>
      // Spread des valeurs + ajout de publish. Une description vide devient null côté API.
      saveLandingPage(camp.id, { ...values, hero_description: values.hero_description.trim() || null, publish }),
    // En cas de succès, on invalide tous les caches qui affichent le camp ou sa publication.
    // void : la promesse n'est pas attendue, on ne veut pas bloquer l'interface.
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['camp', camp.id] })
      void queryClient.invalidateQueries({ queryKey: ['camps'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['public-camps'] })
    },
  })

  // Vrai si le camp est déjà publié : change le libellé des boutons.
  const published = camp.status === 'published'

  return (
    <Card>
      {/* noValidate : la validation est gérée par Zod, pas par le navigateur. */}
      {/* Pas de onSubmit sur le form : les boutons appellent handleSubmit directement. */}
      <form noValidate className="space-y-4">
        <Field label="Thème saisonnier" hint="Change les couleurs et le style du compte à rebours.">
          {(props) => (
            <select {...props} {...register('season_theme')} className={`${inputClass} sm:max-w-xs`}>
              {/* Génère une option par saison à partir du dictionnaire de libellés. */}
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

        {/* save.variables contient les arguments de la dernière sauvegarde : permet de choisir le message de succès. */}
        {save.isSuccess && (
          <Alert tone="success">
            {save.variables?.publish ? 'Landing page publiée : les inscriptions sont ouvertes.' : 'Landing page enregistrée en brouillon.'}
          </Alert>
        )}
        {save.error && <Alert>{save.error.message}</Alert>}

        <div className="flex flex-wrap gap-3">
          {/* handleSubmit valide le formulaire, puis appelle la fonction avec les valeurs. Si la validation échoue, rien n'est envoyé. */}
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

  // Messages de contact reçus pour ce camp.
  const messages = useQuery({ queryKey: ['messages', camp.id], queryFn: () => fetchMessages(camp.id), staleTime: 0 })

  // Changement du statut d'un message (lu, traité...). Recharge la liste après succès.
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
          {/* Bordure colorée pour les messages non lus, afin de les repérer. */}
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
                  // event.target.value est une chaîne : on la convertit en MessageStatus (assertion de type).
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
            {/* whitespace-pre-line : conserve les retours à la ligne saisis par le visiteur. */}
            <p className="mt-3 whitespace-pre-line text-sm">{message.message}</p>
          </Card>
        </li>
      ))}
    </ul>
  )
}

// ---- Onglet Chatbot (données MongoDB) -----------------------------------------

function ChatTab({ camp }: { camp: Camp }) {
  // Statistiques : nombre de conversations, de questions, et intentions les plus fréquentes.
  const stats = useQuery({ queryKey: ['chat-stats', camp.id], queryFn: () => fetchChatStats(camp.id), staleTime: 0 })

  // Dernières conversations. Chargé en parallèle des statistiques.
  const conversations = useQuery({
    queryKey: ['conversations', camp.id],
    queryFn: () => fetchConversations(camp.id),
    staleTime: 0,
  })

  if (stats.isPending) return <Spinner />
  if (stats.isError) return <Alert>{stats.error.message}</Alert>

  // Valeur maximale des intentions, sert de référence pour la largeur des barres.
  // Math.max(1, ...) : évite une division par zéro quand la liste est vide.
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
                  {/* Traduit l'intention, ou affiche le code brut si aucun libellé n'existe. */}
                  <span>{intentLabels[item.intent] ?? item.intent}</span>
                  <span className="font-semibold tabular-nums">{item.count}</span>
                </div>
                {/* Barre de progression décorative : la valeur est déjà donnée par le nombre. */}
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
            // session_id identifie chaque conversation de façon unique.
            <li key={conversation.session_id} className="rounded-xl bg-sand-50 p-3">
              <p className="text-xs text-navy-500">{formatDateTime(conversation.updated_at)}</p>
              <ul className="mt-2 space-y-1 text-sm">
                {/* Seuls les messages du visiteur sont affichés, pas les réponses du bot. */}
                {conversation.messages
                  .filter((message) => message.role === 'visitor')
                  .map((message, index) => (
                    // L'index sert de clé ici : acceptable car la liste n'est pas réordonnée.
                    <li key={index}>
                      « {message.content} »{' '}
                      {/* ?? '' : évite de passer undefined à la table de correspondance. */}
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
  // Identifiant du camp issu de l'URL (ex. /espace/camps/42).
  const { campId = '' } = useParams()

  // Paramètres de l'URL. setSearchParams permet de changer l'onglet sans recharger la page.
  const [searchParams, setSearchParams] = useSearchParams()

  // Onglet actif, lu dans l'URL (?onglet=landing). Par défaut : inscriptions.
  // L'onglet est dans l'URL, donc on peut partager le lien ou actualiser sans perdre sa position.
  const tab = searchParams.get('onglet') ?? 'inscriptions'

  // Données du camp, chargées une seule fois pour toute la page et transmises aux onglets.
  const camp = useQuery({ queryKey: ['camp', campId], queryFn: () => fetchCamp(campId), staleTime: 0 })

  // Titre de l'onglet du navigateur, mis à jour quand le camp est chargé.
  useEffect(() => {
    if (camp.data) document.title = `${camp.data.name} – Espace CampOrga`
  }, [camp.data])

  if (camp.isPending) return <Spinner />
  if (camp.isError) return <Alert>{camp.error.message}</Alert>

  // Raccourci vers les données du camp, typées comme Camp.
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
            {/* Lien vers la page publique : affiché seulement si le camp est publié. */}
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

      {/* Onglets : chaque élément a un id (utilisé dans l'URL), un libellé et son contenu.
          replace: true remplace l'entrée d'historique au lieu d'en ajouter une, pour que le bouton Retour
          du navigateur ne fasse pas défiler les onglets un par un. */}
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