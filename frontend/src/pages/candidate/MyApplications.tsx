import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, ChevronDown, FileText, Trash2, XCircle } from 'lucide-react'
import { api, asCompany, session, type Application, type Job } from '../../api'
import AnalysisPanel from '../../components/Analysis'
import { ScoreRing } from '../../components/charts'
import { Avatar, Button, Card, EmptyState, ErrorBanner, PageHeader, PageSkeleton, StageBadge } from '../../components/ui'
import { buttonClass, cn, STAGES, timeAgo, useFetch } from '../../lib'

const STEPS = STAGES.filter((s) => s.key !== 'rejected')
const NOT_WITHDRAWABLE = ['offer', 'hired', 'rejected']

function Tracker({ status }: { status: string }) {
  if (status === 'rejected') {
    return (
      <p className="flex items-center gap-2 text-sm text-bad">
        <XCircle size={16} /> This application was not taken forward.
      </p>
    )
  }
  const current = STEPS.findIndex((s) => s.key === status)
  return (
    <ol className="flex items-center">
      {STEPS.map((s, i) => {
        const done = i < current
        const active = i === current
        return (
          <li key={s.key} className={cn('flex items-center', i < STEPS.length - 1 && 'flex-1')}>
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={cn(
                  'flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-semibold',
                  done && 'border-good bg-good text-bg',
                  active && 'border-brand bg-brand text-white',
                  !done && !active && 'border-line text-faint',
                )}
              >
                {done ? <Check size={13} /> : i + 1}
              </span>
              <span className={cn('text-[11px]', active ? 'font-medium text-ink' : 'text-faint')}>{s.label}</span>
            </div>
            {i < STEPS.length - 1 && <span className={cn('mx-1 mb-5 h-px flex-1', done ? 'bg-good' : 'bg-line')} />}
          </li>
        )
      })}
    </ol>
  )
}

export default function MyApplications() {
  const { data, error, loading, reload } = useFetch(() => api<{ data: Application[] }>(`/job-application/get-by-candidate/${session.userId}`))
  const [open, setOpen] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  const withdraw = async (id: string) => {
    if (!window.confirm('Withdraw this application? This cannot be undone.')) return
    setActionError(null)
    try {
      await api(`/job-application/withdraw/${id}`, { method: 'POST' })
      reload()
    } catch (e) {
      setActionError((e as Error).message)
    }
  }

  return (
    <>
      <PageHeader title="My applications" subtitle="Follow each application through the hiring process" />
      <ErrorBanner error={actionError} />
      {data.data.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="You have not applied to any jobs yet"
          action={<Link to="/candidate/jobs" className={buttonClass('primary')}>Browse jobs</Link>}
        />
      ) : (
        <div className="space-y-4">
          {data.data.map((a) => {
            const job = typeof a.job === 'object' ? (a.job as Job) : null
            const company = asCompany(a.company)
            const expanded = open === a._id
            return (
              <Card key={a._id}>
                <div className="mb-5 flex items-center gap-4">
                  <Avatar name={company?.name} size={42} />
                  <div className="min-w-0 flex-1">
                    {job ? (
                      <Link to={`/candidate/jobs/${job._id}`} className="font-semibold text-ink hover:text-brand">{job.role}</Link>
                    ) : (
                      <span className="font-semibold text-muted">Job removed</span>
                    )}
                    <p className="text-sm text-muted">{company?.name} - applied {timeAgo(a.createdAt)}</p>
                  </div>
                  <ScoreRing score={a.AIScore} size={44} />
                  <StageBadge stage={a.status} />
                </div>
                <Tracker status={a.status} />

                <div className="mt-4 flex items-center gap-2">
                  {a.analysis && (
                    <Button small variant="ghost" onClick={() => setOpen(expanded ? null : a._id)}>
                      <ChevronDown size={14} className={cn('transition', expanded && 'rotate-180')} />
                      Why this score
                    </Button>
                  )}
                  {!NOT_WITHDRAWABLE.includes(a.status) && (
                    <Button small variant="ghost" icon={Trash2} className="ml-auto text-bad hover:text-bad" onClick={() => withdraw(a._id)}>
                      Withdraw
                    </Button>
                  )}
                </div>
                {expanded && <AnalysisPanel analysis={a.analysis} className="mt-3 border-t border-line pt-4" />}
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
