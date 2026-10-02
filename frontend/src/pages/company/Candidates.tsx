import { useMemo, useState } from 'react'
import { Search, Users } from 'lucide-react'
import { api, type Job, type RecruiterApplication } from '../../api'
import { ScoreRing } from '../../components/charts'
import CandidateDrawer from '../../components/CandidateDrawer'
import { Avatar, Card, Chip, EmptyState, ErrorBanner, PageHeader, PageSkeleton, StageBadge } from '../../components/ui'
import { cn, inputClass, STAGES, timeAgo, useFetch } from '../../lib'

export default function Candidates() {
  const { data, setData, error, loading } = useFetch(() => api<{ data: RecruiterApplication[] }>('/job-application/get-by-company'))
  const [query, setQuery] = useState('')
  const [stage, setStage] = useState('all')
  const [sort, setSort] = useState<'score' | 'recent'>('score')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const apps = useMemo(() => data?.data ?? [], [data])
  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return apps
      .filter((a) => stage === 'all' || a.status === stage)
      .filter((a) => !q || `${a.candidate.fullName} ${a.candidate.email} ${(a.candidate.skills ?? []).join(' ')} ${(a.job as Job).role}`.toLowerCase().includes(q))
      .sort((a, b) => (sort === 'score' ? (b.AIScore ?? 0) - (a.AIScore ?? 0) : +new Date(b.createdAt ?? 0) - +new Date(a.createdAt ?? 0)))
  }, [apps, query, stage, sort])

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  const update = (updated: RecruiterApplication) => setData({ data: apps.map((a) => (a._id === updated._id ? updated : a)) })
  const selected = apps.find((a) => a._id === selectedId) ?? null

  return (
    <>
      <PageHeader title="Candidates" subtitle="Everyone who applied to any of your jobs" />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-60 flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, skill or job" className={cn(inputClass, 'pl-9')} />
        </div>
        <select value={stage} onChange={(e) => setStage(e.target.value)} className={cn(inputClass, 'w-auto')}>
          <option value="all">All stages</option>
          {STAGES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as 'score' | 'recent')} className={cn(inputClass, 'w-auto')}>
          <option value="score">Best match first</option>
          <option value="recent">Most recent first</option>
        </select>
      </div>

      {rows.length === 0 ? (
        <EmptyState icon={Users} title="No candidates found" text="Try a different search or stage filter." />
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="px-5 py-3 font-medium">Candidate</th>
                  <th className="px-5 py-3 font-medium">Job</th>
                  <th className="px-5 py-3 font-medium">Match</th>
                  <th className="px-5 py-3 font-medium">Stage</th>
                  <th className="hidden px-5 py-3 font-medium lg:table-cell">Skills</th>
                  <th className="px-5 py-3 font-medium">Applied</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {rows.map((a) => (
                  <tr key={a._id} onClick={() => setSelectedId(a._id)} className="cursor-pointer transition hover:bg-raised/60">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <Avatar name={a.candidate.fullName ?? a.candidate.email} size={34} />
                        <div>
                          <p className="font-medium text-ink">{a.candidate.fullName || a.candidate.email}</p>
                          <p className="text-xs text-muted">{a.candidate.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-ink">{(a.job as Job).role}</td>
                    <td className="px-5 py-3.5"><ScoreRing score={a.AIScore} size={36} /></td>
                    <td className="px-5 py-3.5"><StageBadge stage={a.status} /></td>
                    <td className="hidden px-5 py-3.5 lg:table-cell">
                      <div className="flex gap-1">{(a.candidate.skills ?? []).slice(0, 2).map((s) => <Chip key={s}>{s}</Chip>)}</div>
                    </td>
                    <td className="px-5 py-3.5 text-muted">{timeAgo(a.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {selected && <CandidateDrawer application={selected} onClose={() => setSelectedId(null)} onChange={update} />}
    </>
  )
}
