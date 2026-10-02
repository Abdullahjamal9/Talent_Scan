import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, JOB_TYPES, type Job } from '../../api'
import { Button, Card, ErrorBanner, Field, PageHeader, PageSkeleton } from '../../components/ui'
import { inputClass, useFetch } from '../../lib'

export default function JobForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const existing = useFetch(async () => (id ? api<Job>(`/job-post/${id}`) : null), [id])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (existing.loading) return <PageSkeleton />
  const job = existing.data

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>
    const payload = { ...f, jobType: f.jobType || null, isAcceptingApplications: f.isAcceptingApplications === 'true' }
    setBusy(true)
    setError(null)
    try {
      if (id) await api('/job-post/edit', { json: { ...payload, id } })
      else await api('/job-post/create', { json: payload })
      navigate('/company/jobs')
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title={id ? 'Edit job' : 'Post a job'} subtitle="Candidates are scored against this description, so be specific about skills." />
      <form onSubmit={submit} className="max-w-3xl">
        <Card className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Role"><input name="role" required defaultValue={job?.role} placeholder="Senior Backend Engineer" className={inputClass} /></Field>
          </div>
          <Field label="Job type">
            <select name="jobType" defaultValue={job?.jobType ?? ''} className={`${inputClass} capitalize`}>
              <option value="">Not specified</option>
              {JOB_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Status">
            <select name="isAcceptingApplications" defaultValue={String(job?.isAcceptingApplications ?? true)} className={inputClass}>
              <option value="true">Accepting applications</option>
              <option value="false">Closed</option>
            </select>
          </Field>
          <div className="sm:col-span-2">
            <Field label="Who can apply" hint="Gender-specific roles are shown clearly on the posting and enforced when candidates apply.">
              <select name="genderRestriction" defaultValue={job?.genderRestriction ?? 'any'} className={inputClass}>
                <option value="any">Everyone</option>
                <option value="female">Female candidates only</option>
                <option value="male">Male candidates only</option>
              </select>
            </Field>
          </div>
          <Field label="Minimum salary"><input name="minimumSalary" defaultValue={job?.minimumSalary} className={inputClass} /></Field>
          <Field label="Maximum salary"><input name="maximumSalary" defaultValue={job?.maximumSalary} className={inputClass} /></Field>
          <Field label="Currency"><input name="payingCurrency" defaultValue={job?.payingCurrency} placeholder="USD" className={inputClass} /></Field>
          <div className="sm:col-span-2">
            <Field label="Description">
              <textarea name="description" rows={9} required defaultValue={job?.description} className={inputClass} />
            </Field>
          </div>
        </Card>
        <div className="mt-4"><ErrorBanner error={error} /></div>
        <div className="mt-5 flex gap-3">
          <Button disabled={busy}>{busy ? 'Saving...' : id ? 'Save changes' : 'Publish job'}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/company/jobs')}>Cancel</Button>
        </div>
      </form>
    </>
  )
}
