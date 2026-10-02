import { useState, type FormEvent } from 'react'
import { api, type Company } from '../../api'
import { Button, Card, ErrorBanner, Field, PageHeader, PageSkeleton, SuccessBanner } from '../../components/ui'
import { inputClass, useFetch } from '../../lib'

export default function CompanyProfile() {
  const { data, error, loading } = useFetch(() => api<{ company: Company }>('/company/me'))
  const [message, setMessage] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return <PageSkeleton />
  const c = data?.company
  if (!c) return <ErrorBanner error={error} />

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>
    setBusy(true)
    setMessage(null)
    setSaveError(null)
    try {
      await api('/company/edit', {
        json: {
          name: f.name,
          about: f.about,
          address: f.address,
          phone: f.phone,
          totalEmployees: Number(f.totalEmployees) || 0,
          socials: { linkedin: f.linkedin, facebook: f.facebook, github: f.github },
        },
      })
      setMessage('Company profile saved.')
    } catch (err) {
      setSaveError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Company profile" subtitle="Candidates see this information on your job postings" />
      <form onSubmit={submit} className="max-w-3xl space-y-4">
        <Card className="grid gap-5 sm:grid-cols-2">
          <Field label="Company name"><input name="name" defaultValue={c.name} required className={inputClass} /></Field>
          <Field label="Email"><input value={c.email} disabled className={inputClass} /></Field>
          <Field label="Phone"><input name="phone" defaultValue={c.phone} className={inputClass} /></Field>
          <Field label="Address"><input name="address" defaultValue={c.address} className={inputClass} /></Field>
          <Field label="Total employees"><input name="totalEmployees" type="number" min={0} defaultValue={c.totalEmployees} className={inputClass} /></Field>
          <div className="sm:col-span-2">
            <Field label="About"><textarea name="about" rows={4} defaultValue={c.about} className={inputClass} /></Field>
          </div>
        </Card>
        <Card className="grid gap-5 sm:grid-cols-3">
          {(['linkedin', 'facebook', 'github'] as const).map((k) => (
            <Field key={k} label={k}>
              <input name={k} type="url" defaultValue={c.socials?.[k]} placeholder="https://" className={inputClass} />
            </Field>
          ))}
        </Card>
        <ErrorBanner error={saveError} />
        <SuccessBanner message={message} />
        <Button disabled={busy}>{busy ? 'Saving...' : 'Save changes'}</Button>
      </form>
    </>
  )
}
