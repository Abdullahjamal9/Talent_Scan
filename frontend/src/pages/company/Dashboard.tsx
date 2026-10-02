import { Link } from 'react-router-dom'
import { Briefcase, CalendarCheck, Sparkles, Trophy, UserPlus, Users } from 'lucide-react'
import { api, type CompanyDashboard } from '../../api'
import { Funnel, ScoreDistribution, ScoreRing, TrendChart } from '../../components/charts'
import { Avatar, Card, CardTitle, EmptyState, ErrorBanner, PageHeader, PageSkeleton, StageBadge, Stat } from '../../components/ui'
import { buttonClass, timeAgo, useFetch } from '../../lib'

export default function Dashboard() {
  const { data, error, loading } = useFetch(() => api<CompanyDashboard>('/dashboard/company'))

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  const { kpis } = data

  if (kpis.totalJobs === 0) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Your hiring overview" />
        <EmptyState
          title="Post your first job"
          text="Once you publish a job, applicants will appear here ranked by AI match score."
          action={<Link to="/company/jobs/new" className={buttonClass('primary')}>Post a job</Link>}
        />
      </>
    )
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Your hiring overview"
        action={<Link to="/company/jobs/new" className={buttonClass('primary')}>Post a job</Link>}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Open jobs" value={kpis.openJobs} icon={Briefcase} hint={`${kpis.totalJobs} total`} color="#7c6cf0" />
        <Stat label="Applicants" value={kpis.totalApplicants} icon={Users} hint={`${kpis.newThisWeek} new this week`} color="#4f8cff" />
        <Stat label="In interviews" value={kpis.inInterview} icon={CalendarCheck} hint="Interview and offer stages" color="#fbbf24" />
        <Stat label="Hired" value={kpis.hired} icon={Trophy} hint={kpis.avgScore != null ? `Avg match ${kpis.avgScore}%` : undefined} color="#34d399" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardTitle title="Applications" hint="New applications over the last 14 days" />
          <TrendChart data={data.trend} />
        </Card>
        <Card>
          <CardTitle title="Hiring funnel" hint="Candidates per stage" />
          <Funnel steps={data.funnel} />
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card>
          <CardTitle title="Match score distribution" hint="How strong is your applicant pool" />
          <ScoreDistribution data={data.scoreBuckets} />
        </Card>

        <Card>
          <CardTitle title="Top candidates" hint="Highest AI match across all jobs" />
          {data.topCandidates.length === 0 ? (
            <p className="text-sm text-muted">No scored applications yet.</p>
          ) : (
            <ul className="space-y-3">
              {data.topCandidates.map((c) => (
                <li key={c.applicationId}>
                  <Link to={`/company/jobs/${c.jobId}/pipeline`} className="flex items-center gap-3 rounded-lg p-1.5 transition hover:bg-raised">
                    <ScoreRing score={c.score} size={40} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-ink">{c.name}</p>
                      <p className="truncate text-xs text-muted">{c.job}</p>
                    </div>
                    <StageBadge stage={c.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardTitle title="Recent activity" hint="Latest applications" />
          {data.recent.length === 0 ? (
            <p className="text-sm text-muted">No applications yet.</p>
          ) : (
            <ul className="space-y-3">
              {data.recent.slice(0, 5).map((r) => (
                <li key={r.applicationId} className="flex items-center gap-3">
                  <Avatar name={r.name} size={34} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-ink"><span className="font-medium">{r.name}</span> <span className="text-muted">applied to</span> {r.job}</p>
                    <p className="text-xs text-faint">{timeAgo(r.createdAt)}</p>
                  </div>
                  <UserPlus size={14} className="text-faint" />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <CardTitle
          title="Jobs"
          hint="Applicants per posting"
          action={<Link to="/company/jobs" className="text-xs font-medium text-brand hover:underline">Manage jobs</Link>}
        />
        <div className="divide-y divide-line">
          {data.jobs.map((j) => (
            <Link key={j.id} to={`/company/jobs/${j.id}/pipeline`} className="flex items-center justify-between gap-4 py-3 transition hover:bg-raised/50">
              <div>
                <p className="text-sm font-medium text-ink">{j.role}</p>
                <p className="text-xs text-muted">{j.isAcceptingApplications ? 'Accepting applications' : 'Closed'}</p>
              </div>
              <div className="flex items-center gap-5 text-sm">
                {j.avgScore != null && (
                  <span className="hidden items-center gap-1.5 text-muted sm:flex"><Sparkles size={14} />{j.avgScore}% avg</span>
                )}
                <span className="w-24 text-right font-medium text-ink">{j.applicants} applicants</span>
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </>
  )
}
