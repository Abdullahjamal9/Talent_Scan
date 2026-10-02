import { useEffect, useState } from 'react'
import { ExternalLink, Mail, MapPin, Phone, RefreshCw, X } from 'lucide-react'
import { api, openResume, type Analysis, type RecruiterApplication } from '../api'
import { cn, STAGES, type Stage } from '../lib'
import { Avatar, Button, Chip, ErrorBanner, ScoreBadge, StageBadge } from './ui'
import { ScoreRing } from './charts'
import AnalysisPanel from './Analysis'

/** Slide-over with the full candidate profile, stage controls and private recruiter notes. */
export default function CandidateDrawer({
  application,
  onClose,
  onChange,
}: {
  application: RecruiterApplication
  onClose: () => void
  onChange: (updated: RecruiterApplication) => void
}) {
  const c = application.candidate
  const [notes, setNotes] = useState(application.notes ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [rescoring, setRescoring] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset the form only when a different application is opened, not after our own save
  useEffect(() => {
    setNotes(application.notes ?? '')
    setSaved(false)
    setError(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application._id])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const setStage = async (stage: Stage) => {
    if (stage === application.status) return
    setError(null)
    try {
      await api(`/job-application/status/${application._id}`, { json: { status: stage } })
      onChange({ ...application, status: stage })
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const rescore = async () => {
    setRescoring(true)
    setError(null)
    try {
      const res = await api<{ AIScore: number | null; analysis: Analysis | null }>(`/job-application/rescore/${application._id}`, { method: 'POST' })
      onChange({ ...application, AIScore: res.AIScore, analysis: res.analysis })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setRescoring(false)
    }
  }

  const showResume = async () => {
    setError(null)
    try {
      await openResume(c._id)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const saveNotes = async () => {
    setSaving(true)
    setError(null)
    try {
      await api(`/job-application/notes/${application._id}`, { json: { notes } })
      onChange({ ...application, notes })
      setSaved(true)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const jobTitle = typeof application.job === 'object' ? application.job.role : null

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <aside className="drawer-enter absolute inset-y-0 right-0 flex w-full max-w-lg flex-col border-l border-line bg-surface shadow-2xl">
        <div className="flex items-start justify-between gap-3 border-b border-line p-5">
          <div className="flex items-center gap-3">
            <Avatar name={c.fullName ?? c.email} size={48} />
            <div>
              <h2 className="text-lg font-semibold text-ink">{c.fullName || c.email}</h2>
              <p className="text-sm text-muted">{jobTitle ? `Applied for ${jobTitle}` : 'Candidate'}</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-raised hover:text-ink" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          <div className="flex items-center gap-4 rounded-xl border border-line bg-raised p-4">
            <ScoreRing score={application.AIScore} size={56} />
            <div>
              <p className="text-xs uppercase tracking-wide text-muted">AI match score</p>
              <div className="mt-1 flex items-center gap-2">
                <ScoreBadge score={application.AIScore} />
                <StageBadge stage={application.status} />
              </div>
            </div>
          </div>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">AI analysis</h3>
              <Button small variant="ghost" icon={RefreshCw} onClick={rescore} disabled={rescoring}>
                {rescoring ? 'Scoring...' : application.analysis ? 'Re-score' : 'Score now'}
              </Button>
            </div>
            {application.analysis ? (
              <AnalysisPanel analysis={application.analysis} />
            ) : (
              <p className="text-sm text-muted">This application has not been scored yet. Use Score now to run the AI analysis.</p>
            )}
          </section>

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Move to stage</h3>
            <div className="flex flex-wrap gap-2">
              {STAGES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setStage(s.key)}
                  className={cn(
                    'rounded-full border px-3 py-1 text-xs font-medium transition',
                    application.status === s.key ? 'text-white' : 'border-line text-muted hover:text-ink',
                  )}
                  style={application.status === s.key ? { background: s.color, borderColor: s.color } : undefined}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </section>

          <section className="space-y-2 text-sm text-muted">
            <p className="flex items-center gap-2"><Mail size={15} />{c.email}</p>
            {c.phone && <p className="flex items-center gap-2"><Phone size={15} />{c.phone}</p>}
            {c.address && <p className="flex items-center gap-2"><MapPin size={15} />{c.address}</p>}
            {c.resume && (
              <button type="button" onClick={showResume} className="inline-flex items-center gap-2 text-brand hover:underline">
                <ExternalLink size={15} />Open resume (PDF)
              </button>
            )}
          </section>

          {c.about && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">About</h3>
              <p className="text-sm leading-relaxed text-ink/90">{c.about}</p>
            </section>
          )}

          {!!c.skills?.length && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Skills</h3>
              <div className="flex flex-wrap gap-1.5">{c.skills.map((s) => <Chip key={s}>{s}</Chip>)}</div>
            </section>
          )}

          {!!c.experience?.length && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Experience</h3>
              <ul className="space-y-2 text-sm">
                {c.experience.map((e, i) => (
                  <li key={i} className="rounded-lg border border-line p-3">
                    <p className="font-medium text-ink">{e.role}</p>
                    <p className="text-muted">{e.company_or_organization}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {!!c.qualification?.length && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Education</h3>
              <ul className="space-y-2 text-sm">
                {c.qualification.map((q, i) => (
                  <li key={i} className="rounded-lg border border-line p-3">
                    <p className="font-medium text-ink">{q.program}</p>
                    <p className="text-muted">{q.institute}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Recruiter notes (private)</h3>
            <textarea
              value={notes}
              onChange={(e) => { setNotes(e.target.value); setSaved(false) }}
              rows={4}
              placeholder="Interview feedback, concerns, next steps..."
              className="w-full rounded-lg border border-line bg-raised px-3 py-2 text-sm text-ink placeholder:text-faint outline-none focus:border-brand focus:ring-2 focus:ring-brand/25"
            />
            <div className="mt-2 flex items-center gap-3">
              <Button small variant="secondary" onClick={saveNotes} disabled={saving || notes === (application.notes ?? '')}>
                {saving ? 'Saving...' : 'Save notes'}
              </Button>
              {saved && <span className="text-xs text-good">Saved</span>}
            </div>
          </section>

          <ErrorBanner error={error} />
        </div>
      </aside>
    </div>
  )
}
