import { useEffect, useState, type FormEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { api, openResume, type Candidate, type Experience, type Qualification } from '../../api'
import { Button, Card, CardTitle, ErrorBanner, Field, PageHeader, PageSkeleton, SuccessBanner } from '../../components/ui'
import { inputClass, useFetch } from '../../lib'

const toMonth = (iso?: string) => (iso ? iso.slice(0, 7) : '')
const toIso = (month?: string) => (month ? `${month}-01T00:00:00` : undefined)

export default function Profile() {
  const { data, error, loading } = useFetch(() => api<{ candidate: Candidate }>('/candidate/me'))
  const [experience, setExperience] = useState<Experience[]>([])
  const [qualification, setQualification] = useState<Qualification[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const c = data?.candidate
  useEffect(() => {
    if (c) {
      setExperience((c.experience ?? []).map((e) => ({ ...e, startDate: toMonth(e.startDate), endDate: toMonth(e.endDate) })))
      setQualification((c.qualification ?? []).map((q) => ({ ...q, startDate: toMonth(q.startDate), endDate: toMonth(q.endDate) })))
    }
  }, [c])

  if (loading) return <PageSkeleton />
  if (!c) return <ErrorBanner error={error} />

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const body = new FormData()
    for (const key of ['fullName', 'phone', 'address', 'age', 'gender', 'about']) body.set(key, String(f.get(key) ?? ''))
    body.set('skills', JSON.stringify(String(f.get('skills')).split(',').map((s) => s.trim()).filter(Boolean)))
    body.set(
      'socials',
      JSON.stringify(Object.fromEntries(['linkedin', 'facebook', 'github'].map((k) => [k, String(f.get(k) ?? '') || null]))),
    )
    const dates = <T extends { startDate?: string; endDate?: string }>(items: T[]) =>
      items.map((i) => ({ ...i, startDate: toIso(i.startDate), endDate: toIso(i.endDate) }))
    body.set('experience', JSON.stringify(dates(experience)))
    body.set('qualification', JSON.stringify(dates(qualification)))
    const resume = f.get('resume') as File
    if (resume && resume.size > 0) body.set('resume', resume)

    setBusy(true)
    setMessage(null)
    setSaveError(null)
    try {
      await api('/candidate/edit', { form: body })
      setMessage('Profile saved.')
    } catch (err) {
      setSaveError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="My profile" subtitle="Recruiters and the AI matcher use this information" />
      <form onSubmit={submit} className="max-w-3xl space-y-4">
        <Card className="grid gap-5 sm:grid-cols-2">
          <Field label="Full name"><input name="fullName" defaultValue={c.fullName} className={inputClass} /></Field>
          <Field label="Email"><input value={c.email} disabled className={inputClass} /></Field>
          <Field label="Phone"><input name="phone" defaultValue={c.phone} className={inputClass} /></Field>
          <Field label="Location"><input name="address" defaultValue={c.address} className={inputClass} /></Field>
          <Field label="Age"><input name="age" defaultValue={c.age} className={inputClass} /></Field>
          <Field label="Gender" hint="Needed to apply to gender-specific roles. Never used for scoring.">
            <select name="gender" defaultValue={c.gender ?? ''} className={inputClass}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </Field>
          <div className="sm:col-span-2">
            <Field label="About you"><textarea name="about" rows={4} defaultValue={c.about} className={inputClass} /></Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Skills" hint="Separate with commas">
              <input name="skills" defaultValue={(c.skills ?? []).join(', ')} className={inputClass} />
            </Field>
          </div>
        </Card>

        <Card className="grid gap-5 sm:grid-cols-3">
          {(['linkedin', 'facebook', 'github'] as const).map((k) => (
            <Field key={k} label={k}>
              <input name={k} type="url" defaultValue={c.socials?.[k]} placeholder="https://" className={inputClass} />
            </Field>
          ))}
        </Card>

        <ListEditor
          title="Experience"
          items={experience}
          onChange={setExperience}
          blank={{ company_or_organization: '', role: '', description: '' }}
          fields={[
            { key: 'role', label: 'Role' },
            { key: 'company_or_organization', label: 'Company' },
            { key: 'startDate', label: 'Start', month: true },
            { key: 'endDate', label: 'End', month: true },
            { key: 'description', label: 'Description', wide: true },
          ]}
        />
        <ListEditor
          title="Education"
          items={qualification}
          onChange={setQualification}
          blank={{ institute: '', program: '', description: '' }}
          fields={[
            { key: 'program', label: 'Degree / program' },
            { key: 'institute', label: 'Institute' },
            { key: 'startDate', label: 'Start', month: true },
            { key: 'endDate', label: 'End', month: true },
          ]}
        />

        <Card>
          <Field label="Replace resume (PDF)">
            <input name="resume" type="file" accept="application/pdf" className="block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-raised file:px-3 file:py-2 file:text-sm file:text-ink" />
          </Field>
          {c.resume && (
            <button type="button" onClick={() => openResume(c._id).catch((e) => setSaveError(e.message))} className="mt-3 inline-block text-sm text-brand hover:underline">
              View current resume
            </button>
          )}
        </Card>

        <ErrorBanner error={saveError} />
        <SuccessBanner message={message} />
        <Button disabled={busy}>{busy ? 'Saving...' : 'Save profile'}</Button>
      </form>
    </>
  )
}

interface FieldDef {
  key: string
  label: string
  month?: boolean
  wide?: boolean
}

function ListEditor<T extends Record<string, any>>({
  title, items, onChange, blank, fields,
}: {
  title: string
  items: T[]
  onChange: (items: T[]) => void
  blank: T
  fields: FieldDef[]
}) {
  const update = (i: number, key: string, value: string) => onChange(items.map((it, idx) => (idx === i ? { ...it, [key]: value } : it)))

  return (
    <Card>
      <CardTitle
        title={title}
        action={<Button type="button" small variant="secondary" icon={Plus} onClick={() => onChange([...items, { ...blank }])}>Add</Button>}
      />
      {items.length === 0 && <p className="text-sm text-muted">Nothing added yet.</p>}
      <div className="space-y-4">
        {items.map((item, i) => (
          <div key={i} className="grid gap-4 rounded-lg border border-line bg-raised/40 p-4 sm:grid-cols-2">
            {fields.map((f) => (
              <div key={f.key} className={f.wide ? 'sm:col-span-2' : ''}>
                <Field label={f.label}>
                  <input
                    type={f.month ? 'month' : 'text'}
                    value={item[f.key] ?? ''}
                    onChange={(e) => update(i, f.key, e.target.value)}
                    className={inputClass}
                  />
                </Field>
              </div>
            ))}
            <div>
              <Button type="button" small variant="danger" icon={Trash2} onClick={() => onChange(items.filter((_, idx) => idx !== i))}>Remove</Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
