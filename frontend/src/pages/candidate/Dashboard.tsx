import { Link } from 'react-router-dom'
import { FileText, MessageSquare, Send, Sparkles, Trophy } from 'lucide-react'
import { api, asCompany, type CandidateDashboard } from '../../api'
import { Funnel, ScoreRing } from '../../components/charts'
import { Badge, Card, CardTitle, EmptyState, ErrorBanner, PageHeader, PageSkeleton, ProgressBar, StageBadge, Stat } from '../../components/ui'
import { buttonClass, scoreColor, timeAgo, useFetch } from '../../lib'

export default function Dashboard() {
  const { data, error, loading } = useFetch(() => api<CandidateDashboard>('/dashboard/candidate'))

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  const { kpis, profile } = data

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Track your applications and find your next role"
        action={<Link to="/candidate/jobs" className={buttonClass('primary')}>Find jobs</Link>}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Applications" value={kpis.applications} icon={Send} hint={`${kpis.active} still active`} color="#7c6cf0" />
        <Stat label="Interviews" value={kpis.interviews} icon={MessageSquare} color="#4f8cff" />
        <Stat label="Offers" value={kpis.offers} icon={Trophy} color="#34d399" />
        <Stat label="Avg match" value={kpis.avgScore != null ? `${kpis.avgScore}%` : '-'} icon={Sparkles} hint="Across your applications" color="#fbbf24" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardTitle
            title="Recent applications"
            action={<Link to="/candidate/applications" className="text-xs font-medium text-brand hover:underline">View all</Link>}
          />
          {data.recent.length === 0 ? (
            <EmptyState icon={FileText} title="No applications yet" text="Apply to a job and track its progress here." action={<Link to="/candidate/jobs" className={buttonClass('primary', true)}>Browse jobs</Link>} />
          ) : (
            <ul className="divide-y divide-line">
              {data.recent.map((a) => (
                <li key={a.applicationId}>
                  <Link to={`/candidate/jobs/${a.jobId}`} className="flex items-center gap-4 py-3 transition hover:bg-raised/50">
                    <ScoreRing score={a.score} size={42} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-ink">{a.role}</p>
                      <p className="truncate text-xs text-muted">{a.company} - {timeAgo(a.createdAt)}</p>
                    </div>
                    <StageBadge stage={a.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-4">
          <Card>
            <CardTitle title="Profile strength" hint="Complete profiles get better matches" />
            <div className="flex items-center gap-4">
              <ScoreRing score={profile.percent} size={64} />
              <div className="flex-1">
                <ProgressBar value={profile.percent} color={scoreColor(profile.percent)} />
                <p className="mt-2 text-xs text-muted">{profile.percent === 100 ? 'Your profile is complete.' : 'Add the missing details below.'}</p>
              </div>
            </div>
            {profile.missing.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {profile.missing.map((m) => <Badge key={m} color="#fbbf24">{m}</Badge>)}
              </div>
            )}
            {profile.missing.length > 0 && (
              <Link to="/candidate/profile" className={`${buttonClass('secondary', true)} mt-4`}>Complete profile</Link>
            )}
          </Card>

          <Card>
            <CardTitle title="Pipeline" hint="Your applications by stage" />
            <Funnel steps={data.funnel} />
          </Card>
        </div>
      </div>

      <Card className="mt-4">
        <CardTitle title="Recommended for you" hint="Based on the skills in your profile" />
        {data.recommended.length === 0 ? (
          <p className="text-sm text-muted">Add skills to your profile to get recommendations.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {data.recommended.map((j) => (
              <Link key={j._id} to={`/candidate/jobs/${j._id}`} className="rounded-lg border border-line bg-raised p-4 transition hover:border-brand">
                <Badge color="#7c6cf0">{Math.round(j.matchScore ?? 0)}% skill match</Badge>
                <p className="mt-3 text-sm font-semibold text-ink">{j.role}</p>
                <p className="text-xs text-muted">{asCompany(j.company)?.name}</p>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </>
  )
}
