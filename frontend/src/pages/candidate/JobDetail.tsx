import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Building2, CheckCircle2, Lock, MapPin, Wallet } from 'lucide-react'
import { api, asCompany, session, type Analysis, type Application, type Job } from '../../api'
import AnalysisPanel from '../../components/Analysis'
import { ScoreRing } from '../../components/charts'
import { Avatar, Button, Card, CardTitle, Chip, ErrorBanner, GenderBadge, PageSkeleton, StageBadge } from '../../components/ui'
import { buttonClass, formatSalary, timeAgo, useFetch } from '../../lib'

export default function JobDetail() {
  const { id } = useParams()
  const job = useFetch(() => api<Job>(`/job-post/${id}`), [id])
  const mine = useFetch(() => api<{ data: Application[] }>(`/job-application/get-by-candidate/${session.userId}`), [])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [applied, setApplied] = useState<{ score: number | null; analysis: Analysis | null } | null>(null)

  if (job.loading || mine.loading) return <PageSkeleton />
  if (!job.data) return <ErrorBanner error={job.error ?? 'Job not found'} />

  const j = job.data
  const company = asCompany(j.company)
  const existing = mine.data?.data.find((a) => (typeof a.job === 'object' ? a.job._id : a.job) === j._id)
  const result = applied ?? (existing ? { score: existing.AIScore, analysis: existing.analysis ?? null } : null)
  const salary = formatSalary(j.minimumSalary, j.maximumSalary, j.payingCurrency)
  const restriction = j.genderRestriction === 'female' ? 'female' : j.genderRestriction === 'male' ? 'male' : null

  const apply = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await api<{ AIScore: number | null; analysis: Analysis | null }>('/job-application/apply', { json: { job: j._id } })
      setApplied({ score: res.AIScore, analysis: res.analysis })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link to="/candidate/jobs" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft size={14} /> All jobs
      </Link>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex items-start gap-4">
            <Avatar name={company?.name} size={52} />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-ink">{j.role}</h1>
              <p className="text-muted">{company?.name} - posted {timeAgo(j.createdAt)}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {j.jobType && <Chip className="capitalize">{j.jobType}</Chip>}
            <GenderBadge restriction={j.genderRestriction} />
            {salary && <span className="inline-flex items-center gap-1 text-sm text-muted"><Wallet size={14} />{salary}</span>}
          </div>
          <h2 className="mb-2 mt-6 text-sm font-semibold text-ink">About the role</h2>
          <p className="whitespace-pre-line text-sm leading-relaxed text-ink/85">{j.description}</p>
        </Card>

        <div className="space-y-4">
          <Card>
            {result ? (
              <div className="text-center">
                <CheckCircle2 className="mx-auto text-good" size={28} />
                <p className="mt-2 font-semibold text-ink">Application sent</p>
                <div className="mt-4 flex items-center justify-center gap-3">
                  <ScoreRing score={result.score} size={56} />
                  <div className="text-left">
                    <p className="text-xs text-muted">AI match score</p>
                    {existing && <StageBadge stage={existing.status} />}
                  </div>
                </div>
                <Link to="/candidate/applications" className="mt-4 inline-block text-sm text-brand hover:underline">Track in My applications</Link>
              </div>
            ) : j.isAcceptingApplications === false ? (
              <p className="text-center text-sm text-muted">This job is closed to applications.</p>
            ) : j.eligibility === 'not_eligible' ? (
              <div className="text-center">
                <Lock className="mx-auto text-muted" size={24} />
                <p className="mt-2 text-sm font-medium text-ink">This role is open to {restriction} candidates only.</p>
                <p className="mt-1 text-xs text-muted">The company has set this requirement for the position.</p>
              </div>
            ) : j.eligibility === 'gender_missing' ? (
              <div className="text-center">
                <Lock className="mx-auto text-muted" size={24} />
                <p className="mt-2 text-sm font-medium text-ink">This role is open to {restriction} candidates only.</p>
                <p className="mt-1 text-xs text-muted">Please set your gender in your profile to apply.</p>
                <Link to="/candidate/profile" className={`${buttonClass('secondary', true)} mt-3`}>Update profile</Link>
              </div>
            ) : (
              <>
                <CardTitle title="Interested?" hint="We score your profile against this job when you apply." />
                <Button onClick={apply} disabled={busy} className="w-full">{busy ? 'Analysing your profile...' : 'Apply with my profile'}</Button>
              </>
            )}
            <div className="mt-3"><ErrorBanner error={error} /></div>
          </Card>

          {result?.analysis && (
            <Card>
              <CardTitle title="Why this score" hint="How your profile compares with the requirements" />
              <AnalysisPanel analysis={result.analysis} />
            </Card>
          )}

          {company && (
            <Card>
              <CardTitle title={`About ${company.name}`} />
              {company.about && <p className="text-sm leading-relaxed text-muted">{company.about}</p>}
              <div className="mt-3 space-y-1.5 text-sm text-muted">
                {company.address && <p className="flex items-center gap-2"><MapPin size={14} />{company.address}</p>}
                {!!company.totalEmployees && <p className="flex items-center gap-2"><Building2 size={14} />{company.totalEmployees} employees</p>}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  )
}
