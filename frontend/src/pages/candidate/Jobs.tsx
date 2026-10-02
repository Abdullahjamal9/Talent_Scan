import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Briefcase, Search, Wallet } from 'lucide-react'
import { api, asCompany, JOB_TYPES, type Job } from '../../api'
import { Avatar, Badge, Card, Chip, EmptyState, ErrorBanner, GenderBadge, PageHeader, PageSkeleton } from '../../components/ui'
import { cn, formatSalary, inputClass, timeAgo, useFetch } from '../../lib'

export default function Jobs() {
  const { data, error, loading } = useFetch(() => api<{ jobs: Job[] }>('/job-post/recommended_list'))
  const [query, setQuery] = useState('')
  const [type, setType] = useState('all')

  const jobs = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (data?.jobs ?? []).filter(
      (j) =>
        (type === 'all' || j.jobType === type) &&
        (!q || `${j.role} ${j.description} ${asCompany(j.company)?.name}`.toLowerCase().includes(q)),
    )
  }, [data, query, type])

  if (loading) return <PageSkeleton />
  if (!data) return <ErrorBanner error={error} />

  return (
    <>
      <PageHeader title="Find jobs" subtitle="Ranked by how well your skills match each role" />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-60 flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by role, company or keyword" className={cn(inputClass, 'pl-9')} />
        </div>
      </div>
      <div className="mb-6 flex flex-wrap gap-2">
        {['all', ...JOB_TYPES].map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs font-medium capitalize transition',
              type === t ? 'border-brand bg-brand/15 text-white' : 'border-line text-muted hover:text-ink',
            )}
          >
            {t === 'all' ? 'All types' : t}
          </button>
        ))}
      </div>

      {jobs.length === 0 ? (
        <EmptyState icon={Briefcase} title="No jobs found" text="Try a different search or filter." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {jobs.map((job) => {
            const company = asCompany(job.company)
            const salary = formatSalary(job.minimumSalary, job.maximumSalary, job.payingCurrency)
            return (
              <Link key={job._id} to={`/candidate/jobs/${job._id}`} className="group block">
                <Card className="h-full transition group-hover:border-brand/60">
                  <div className="flex items-start gap-3">
                    <Avatar name={company?.name} size={42} />
                    <div className="min-w-0 flex-1">
                      <h2 className="truncate font-semibold text-ink">{job.role}</h2>
                      <p className="truncate text-sm text-muted">{company?.name ?? 'Company'}</p>
                    </div>
                    {!!job.matchScore && <Badge color="#7c6cf0">{Math.round(job.matchScore)}% match</Badge>}
                  </div>
                  {job.eligibility === 'not_eligible' && (
                    <p className="mt-3 text-xs text-warn">You are not eligible for this role.</p>
                  )}
                  <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-muted">{job.description}</p>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {job.jobType && <Chip className="capitalize">{job.jobType}</Chip>}
                    <GenderBadge restriction={job.genderRestriction} />
                    {salary && <span className="inline-flex items-center gap-1 text-xs text-muted"><Wallet size={12} />{salary}</span>}
                    <span className="ml-auto text-xs text-faint">{timeAgo(job.createdAt)}</span>
                  </div>
                  {!!job.matchedSkills?.length && (
                    <div className="mt-3 flex flex-wrap gap-1.5 border-t border-line pt-3">
                      {job.matchedSkills.slice(0, 4).map((s) => <Badge key={s} color="#34d399">{s}</Badge>)}
                    </div>
                  )}
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </>
  )
}
