import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { useAuth } from '../auth'
import type { Role } from '../api'
import { Brand } from '../components/Layout'
import { Button, ErrorBanner, Field } from '../components/ui'
import { cn, inputClass } from '../lib'

const perks: Record<Role, string[]> = {
  candidate: [
    'Upload your resume once - we fill in your profile',
    'See how well you match every job before you apply',
    'Track each application from applied to offer',
  ],
  company: [
    'Applicants ranked automatically by AI match score',
    'Drag-and-drop pipeline with private recruiter notes',
    'Dashboards for applicant trends and conversion',
  ],
}

function Shell({ title, subtitle, role, children, footer }: { title: string; subtitle: string; role: Role; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-bg lg:grid-cols-2">
      <div className="glow relative hidden flex-col justify-between border-r border-line p-12 lg:flex">
        <Brand />
        <div>
          <h2 className="max-w-md text-3xl font-bold leading-tight text-ink">
            {role === 'company' ? 'Run your hiring like a product.' : 'Land your next role with less guesswork.'}
          </h2>
          <ul className="mt-8 space-y-4">
            {perks[role].map((p) => (
              <li key={p} className="flex items-start gap-3 text-muted">
                <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-good" />
                {p}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-faint">Talent Scan &middot; Applicant tracking system</p>
      </div>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden"><Brand /></div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
          <p className="mb-6 mt-1 text-sm text-muted">{subtitle}</p>
          {children}
          <p className="mt-6 text-center text-sm text-muted">{footer}</p>
        </div>
      </div>
    </div>
  )
}

function RoleToggle({ role, onChange }: { role: Role; onChange: (r: Role) => void }) {
  return (
    <div className="mb-5 grid grid-cols-2 rounded-lg border border-line bg-surface p-1 text-sm">
      {(['candidate', 'company'] as Role[]).map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onChange(r)}
          className={cn('rounded-md py-1.5 font-medium transition', role === r ? 'bg-raised text-ink shadow' : 'text-muted hover:text-ink')}
        >
          {r === 'candidate' ? 'Job seeker' : 'Company'}
        </button>
      ))}
    </div>
  )
}

export function Login() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const role: Role = params.get('as') === 'company' ? 'company' : 'candidate'
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (auth.role) return <Navigate to={`/${auth.role}`} replace />

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    try {
      await auth.signIn(role, String(f.get('email')), String(f.get('password')))
      navigate(`/${role}`)
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <Shell
      role={role}
      title="Welcome back"
      subtitle="Sign in to continue to Talent Scan."
      footer={<>No account? <Link className="font-medium text-brand hover:underline" to={`/signup?as=${role}`}>Sign up</Link></>}
    >
      <RoleToggle role={role} onChange={(r) => setParams({ as: r })} />
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email"><input name="email" type="email" required autoComplete="email" className={inputClass} /></Field>
        <Field label="Password"><input name="password" type="password" required autoComplete="current-password" className={inputClass} /></Field>
        <ErrorBanner error={error} />
        <Button disabled={busy} className="w-full">{busy ? 'Signing in...' : 'Sign in'}</Button>
      </form>
    </Shell>
  )
}

export function SignUp() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const role: Role = params.get('as') === 'company' ? 'company' : 'candidate'
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [fileName, setFileName] = useState('')

  if (auth.role) return <Navigate to={`/${auth.role}`} replace />

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    try {
      if (role === 'candidate') {
        await auth.signUpCandidate(form)
        navigate('/candidate/profile')
      } else {
        await auth.signUpCompany({
          name: String(form.get('name')),
          email: String(form.get('email')),
          password: String(form.get('password')),
        })
        navigate('/company/profile')
      }
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <Shell
      role={role}
      title="Create your account"
      subtitle={role === 'candidate' ? 'Upload your resume and we will build your profile.' : 'Start tracking applicants in minutes.'}
      footer={<>Already registered? <Link className="font-medium text-brand hover:underline" to={`/login?as=${role}`}>Sign in</Link></>}
    >
      <RoleToggle role={role} onChange={(r) => setParams({ as: r })} />
      <form onSubmit={submit} className="space-y-4" key={role}>
        <Field label={role === 'candidate' ? 'Full name' : 'Company name'}>
          <input name={role === 'candidate' ? 'fullName' : 'name'} required className={inputClass} />
        </Field>
        <Field label="Email"><input name="email" type="email" required autoComplete="email" className={inputClass} /></Field>
        <Field label="Password" hint="At least 7 characters">
          <input name="password" type="password" required minLength={7} autoComplete="new-password" className={inputClass} />
        </Field>
        {role === 'candidate' && (
          <Field label="Gender (optional)" hint="Only needed for roles open to one gender. It is never used to score you.">
            <select name="gender" defaultValue="" className={inputClass}>
              <option value="">Prefer not to say</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
          </Field>
        )}
        {role === 'candidate' && (
          <Field label="Resume (PDF, max 5MB)">
            <label className="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-line bg-raised px-3 py-4 text-sm text-muted transition hover:border-brand hover:text-ink">
              {fileName || 'Click to choose a PDF'}
              <input
                name="resume"
                type="file"
                accept="application/pdf"
                required
                className="sr-only"
                onChange={(e) => setFileName(e.target.files?.[0]?.name ?? '')}
              />
            </label>
          </Field>
        )}
        <ErrorBanner error={error} />
        <Button disabled={busy} className="w-full">
          {busy ? (role === 'candidate' ? 'Reading your resume...' : 'Creating...') : 'Create account'}
        </Button>
      </form>
    </Shell>
  )
}
