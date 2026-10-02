import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Search } from 'lucide-react'
import { api, type Job, type RecruiterApplication } from '../../api'
import { ScoreRing } from '../../components/charts'
import CandidateDrawer from '../../components/CandidateDrawer'
import { Avatar, Chip, EmptyState, ErrorBanner, PageSkeleton } from '../../components/ui'
import { cn, inputClass, STAGES, useFetch, type Stage } from '../../lib'

export default function Pipeline() {
  const { id } = useParams()
  const job = useFetch(() => api<Job>(`/job-post/${id}`), [id])
  const list = useFetch(() => api<{ data: RecruiterApplication[] }>(`/job-application/get-by-company-and-job/${id}`), [id])
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [dragId, setDragId] = useState<string | null>(null)
  const [overStage, setOverStage] = useState<Stage | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const apps = useMemo(() => list.data?.data ?? [], [list.data])
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return apps.filter((a) => !q || `${a.candidate.fullName} ${a.candidate.email} ${(a.candidate.skills ?? []).join(' ')}`.toLowerCase().includes(q))
  }, [apps, query])

  if (list.loading || job.loading) return <PageSkeleton />
  if (!list.data) return <ErrorBanner error={list.error} />

  const update = (updated: RecruiterApplication) =>
    list.setData({ data: apps.map((a) => (a._id === updated._id ? updated : a)) })

  const moveTo = async (appId: string, stage: Stage) => {
    const current = apps.find((a) => a._id === appId)
    if (!current || current.status === stage) return
    setActionError(null)
    update({ ...current, status: stage }) // optimistic
    try {
      await api(`/job-application/status/${appId}`, { json: { status: stage } })
    } catch (e) {
      update(current) // roll back
      setActionError((e as Error).message)
    }
  }

  const selected = apps.find((a) => a._id === selectedId) ?? null

  return (
    <div className="flex flex-col">
      <Link to="/company/jobs" className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft size={14} /> Jobs
      </Link>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">{job.data?.role ?? 'Pipeline'}</h1>
          <p className="mt-1 text-sm text-muted">{apps.length} applicant{apps.length === 1 ? '' : 's'} - drag cards between stages</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name or skill" className={cn(inputClass, 'pl-9')} />
        </div>
      </div>

      <ErrorBanner error={actionError} />

      {apps.length === 0 ? (
        <EmptyState title="No applicants yet" text="Candidates who apply to this job will show up here, ranked by AI match." />
      ) : (
        <div className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-4 sm:-mx-8 sm:px-8">
          {STAGES.map((stage) => {
            const cards = visible.filter((a) => a.status === stage.key).sort((a, b) => (b.AIScore ?? 0) - (a.AIScore ?? 0))
            return (
              <section
                key={stage.key}
                onDragOver={(e) => { e.preventDefault(); setOverStage(stage.key) }}
                onDragLeave={() => setOverStage((s) => (s === stage.key ? null : s))}
                onDrop={() => {
                  if (dragId) moveTo(dragId, stage.key)
                  setDragId(null)
                  setOverStage(null)
                }}
                className={cn(
                  'flex min-h-[60vh] w-64 shrink-0 flex-col rounded-xl border bg-surface transition xl:min-w-56 xl:flex-1',
                  overStage === stage.key ? 'border-brand bg-brand/5' : 'border-line',
                )}
              >
                <header className="flex items-center justify-between border-b border-line px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full" style={{ background: stage.color }} />
                    <h2 className="text-sm font-semibold text-ink">{stage.label}</h2>
                  </div>
                  <span className="rounded-full bg-raised px-2 py-0.5 text-xs text-muted">{cards.length}</span>
                </header>
                <div className="flex min-h-32 flex-1 flex-col gap-2.5 p-2.5">
                  {cards.map((a) => (
                    <article
                      key={a._id}
                      draggable
                      onDragStart={() => setDragId(a._id)}
                      onDragEnd={() => { setDragId(null); setOverStage(null) }}
                      onClick={() => setSelectedId(a._id)}
                      className={cn(
                        'cursor-grab rounded-lg border border-line bg-raised p-3 transition hover:border-faint active:cursor-grabbing',
                        dragId === a._id && 'opacity-40',
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar name={a.candidate.fullName ?? a.candidate.email} size={34} />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-ink">{a.candidate.fullName || a.candidate.email}</p>
                          <p className="truncate text-xs text-muted">{a.candidate.email}</p>
                        </div>
                        <ScoreRing score={a.AIScore} size={38} />
                      </div>
                      {!!a.candidate.skills?.length && (
                        <div className="mt-2.5 flex flex-wrap gap-1">
                          {a.candidate.skills.slice(0, 3).map((s) => <Chip key={s}>{s}</Chip>)}
                          {a.candidate.skills.length > 3 && <Chip>+{a.candidate.skills.length - 3}</Chip>}
                        </div>
                      )}
                    </article>
                  ))}
                  {cards.length === 0 && <p className="m-auto text-xs text-faint">Drop candidates here</p>}
                </div>
              </section>
            )
          })}
        </div>
      )}

      {selected && <CandidateDrawer application={selected} onClose={() => setSelectedId(null)} onChange={update} />}
    </div>
  )
}
