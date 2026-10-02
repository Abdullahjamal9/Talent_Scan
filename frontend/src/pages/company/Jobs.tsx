import { Link } from 'react-router-dom'
import { Kanban, Pencil, Plus } from 'lucide-react'
import { api, type CompanyDashboard } from '../../api'
import { Badge, Button, Card, EmptyState, ErrorBanner, GenderBadge, PageHeader, PageSkeleton } from '../../components/ui'
import { buttonClass, timeAgo, useFetch } from '../../lib'

export default function CompanyJobs() {
  const { data, error, loading, reload } = useFetch(() => api<CompanyDashboard>('/dashboard/company'))

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  const toggle = async (id: string, open: boolean) => {
    await api('/job-post/edit', { json: { id, isAcceptingApplications: !open } })
    reload()
  }

  return (
    <>
      <PageHeader
        title="Jobs"
        subtitle="Manage your postings and open their hiring pipeline"
        action={<Link to="/company/jobs/new" className={buttonClass('primary')}><Plus size={16} />Post a job</Link>}
      />

      {data.jobs.length === 0 ? (
        <EmptyState title="No jobs yet" text="Post a job to start receiving applications." />
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Applicants</th>
                  <th className="px-5 py-3 font-medium">Avg match</th>
                  <th className="px-5 py-3 font-medium">Posted</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {[...data.jobs].reverse().map((j) => (
                  <tr key={j.id} className="transition hover:bg-raised/50">
                    <td className="px-5 py-4">
                      <p className="font-medium text-ink">{j.role}</p>
                      <p className="text-xs capitalize text-muted">{j.jobType ?? 'Not specified'}</p>
                      <div className="mt-1"><GenderBadge restriction={j.genderRestriction} /></div>
                    </td>
                    <td className="px-5 py-4">
                      <Badge color={j.isAcceptingApplications ? '#34d399' : '#8a90a2'}>{j.isAcceptingApplications ? 'Open' : 'Closed'}</Badge>
                    </td>
                    <td className="px-5 py-4 text-ink">{j.applicants}</td>
                    <td className="px-5 py-4 text-muted">{j.avgScore != null ? `${j.avgScore}%` : '-'}</td>
                    <td className="px-5 py-4 text-muted">{timeAgo(j.createdAt)}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <Link to={`/company/jobs/${j.id}/pipeline`} className={buttonClass('primary', true)}><Kanban size={14} />Pipeline</Link>
                        <Link to={`/company/jobs/${j.id}/edit`} className={buttonClass('secondary', true)}><Pencil size={14} />Edit</Link>
                        <Button small variant="ghost" onClick={() => toggle(j.id, j.isAcceptingApplications)}>
                          {j.isAcceptingApplications ? 'Close' : 'Reopen'}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  )
}
