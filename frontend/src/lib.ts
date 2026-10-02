import { useEffect, useState } from 'react'

export function cn(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(' ')
}

// ---- Styles shared by inputs and buttons ----

export const inputClass =
  'w-full rounded-lg border border-line bg-raised px-3 py-2 text-sm text-ink placeholder:text-faint outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/25 disabled:opacity-60'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-brand-gradient text-white shadow-lg shadow-brand/20 hover:brightness-110',
  secondary: 'border border-line bg-raised text-ink hover:border-faint hover:bg-surface',
  ghost: 'text-muted hover:bg-raised hover:text-ink',
  danger: 'border border-bad/30 bg-bad/10 text-bad hover:bg-bad/20',
}

export function buttonClass(variant: ButtonVariant = 'primary', small = false) {
  return cn(
    'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition disabled:pointer-events-none disabled:opacity-50',
    small ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm',
    buttonVariants[variant],
  )
}

// ---- Hiring pipeline ----

export type Stage = 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'

export const STAGES: { key: Stage; label: string; color: string }[] = [
  { key: 'applied', label: 'Applied', color: '#8a90a2' },
  { key: 'screening', label: 'Screening', color: '#38bdf8' },
  { key: 'interview', label: 'Interview', color: '#7c6cf0' },
  { key: 'offer', label: 'Offer', color: '#fbbf24' },
  { key: 'hired', label: 'Hired', color: '#34d399' },
  { key: 'rejected', label: 'Rejected', color: '#f87171' },
]

export const stageMeta = (stage: string) => STAGES.find((s) => s.key === stage) ?? STAGES[0]

export const scoreColor = (score: number) => (score >= 75 ? '#34d399' : score >= 50 ? '#fbbf24' : '#f87171')

// ---- Formatting ----

export function formatSalary(min?: string, max?: string, currency?: string) {
  if (!min && !max) return null
  return `${currency ?? ''} ${[min, max].filter(Boolean).join(' - ')}`.trim()
}

export function timeAgo(iso?: string | null) {
  if (!iso) return ''
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  const units: [number, string][] = [[86400 * 30, 'mo'], [86400, 'd'], [3600, 'h'], [60, 'm']]
  for (const [size, label] of units) {
    if (seconds >= size) return `${Math.floor(seconds / size)}${label} ago`
  }
  return 'just now'
}

export function initials(name?: string) {
  return (name ?? '?')
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join('')
}

// ---- Data loading ----

/** Loads data on mount (and when deps change) with loading/error state. */
export function useFetch<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    load()
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, version])

  return { data, setData, error, loading, reload: () => setVersion((v) => v + 1) }
}
