/**
 * Petits composants d'interface réutilisés partout (bouton, champ, alerte...).
 * Ils centralisent le style ET l'accessibilité : un seul endroit à corriger.
 */
import { useId, type ButtonHTMLAttributes, type ReactElement, type ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import type { CampStatus } from '../api/types'
import { statusLabels } from '../lib/format'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

const variants: Record<Variant, string> = {
  primary: 'bg-coral-600 text-white hover:bg-coral-700 shadow-sm',
  secondary: 'bg-white text-navy-900 ring-1 ring-navy-100 hover:bg-navy-50',
  danger: 'bg-white text-coral-700 ring-1 ring-coral-100 hover:bg-coral-100',
  ghost: 'text-navy-700 hover:bg-navy-50',
}

const base =
  'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ' +
  'disabled:cursor-not-allowed disabled:opacity-60'

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />
}

export function LinkButton({ variant = 'primary', className = '', ...props }: LinkProps & { variant?: Variant }) {
  return <Link className={`${base} ${variants[variant]} ${className}`} {...props} />
}

export const inputClass =
  'block w-full rounded-xl border border-navy-100 bg-white px-3.5 py-2.5 text-sm text-navy-900 ' +
  'placeholder:text-navy-500/60 focus:border-coral-400 focus:outline-none focus:ring-2 focus:ring-coral-100 ' +
  'aria-[invalid=true]:border-coral-600'

/**
 * Champ de formulaire accessible : relie le label, l'aide et l'erreur au champ
 * (htmlFor / aria-describedby / aria-invalid) pour les lecteurs d'écran.
 */
export function Field({
  label,
  error,
  hint,
  required,
  children,
}: {
  label: string
  error?: string
  hint?: string
  required?: boolean
  children: (props: { id: string; 'aria-invalid': boolean; 'aria-describedby'?: string }) => ReactElement
}) {
  const id = useId()
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-navy-900">
        {label}
        {required && (
          <span className="text-coral-600" aria-hidden="true">
            {' '}*
          </span>
        )}
      </label>
      {children({ id, 'aria-invalid': Boolean(error), 'aria-describedby': describedBy })}
      {hint && !error && (
        <p id={`${id}-hint`} className="text-xs text-navy-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-xs font-medium text-coral-700">
          {error}
        </p>
      )}
    </div>
  )
}

export function Alert({ tone = 'error', children }: { tone?: 'error' | 'success' | 'info'; children: ReactNode }) {
  const tones = {
    error: 'bg-coral-100 text-coral-700 ring-coral-400/40',
    success: 'bg-spring-soft text-spring ring-spring/30',
    info: 'bg-navy-50 text-navy-700 ring-navy-100',
  }
  // role="alert" fait lire immédiatement les erreurs ; "status" est plus discret.
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-xl px-4 py-3 text-sm ring-1 ${tones[tone]}`}>
      {children}
    </div>
  )
}

export function Spinner({ label = 'Chargement…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-12 text-sm text-navy-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-navy-100 border-t-coral-600" aria-hidden="true" />
      {label}
    </div>
  )
}

export function Card({ className = '', children }: { className?: string; children: ReactNode }) {
  return <section className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-navy-100 sm:p-6 ${className}`}>{children}</section>
}

export function StatusBadge({ status }: { status: CampStatus }) {
  const styles: Record<CampStatus, string> = {
    draft: 'bg-navy-50 text-navy-700',
    published: 'bg-spring-soft text-spring',
    archived: 'bg-sand-100 text-navy-500',
  }
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[status]}`}>
      {statusLabels[status]}
    </span>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-navy-100 px-6 py-12 text-center">
      <p className="font-display text-lg font-semibold">{title}</p>
      {children && <div className="mt-2 text-sm text-navy-500">{children}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>
        {subtitle && <div className="mt-1 text-sm text-navy-500">{subtitle}</div>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
