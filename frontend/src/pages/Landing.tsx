import { Link, Navigate } from 'react-router-dom'
import { ArrowRight, BarChart3, Kanban, Sparkles } from 'lucide-react'
import { useAuth } from '../auth'
import { Brand } from '../components/Layout'
import { buttonClass } from '../lib'

const features = [
  {
    icon: Sparkles,
    title: 'AI resume matching',
    text: 'Every application is parsed and scored against the job, so the best fits rise to the top.',
  },
  {
    icon: Kanban,
    title: 'Visual hiring pipeline',
    text: 'Drag candidates from applied to hired. Add private notes and keep every stage in one place.',
  },
  {
    icon: BarChart3,
    title: 'Hiring dashboards',
    text: 'See applicant trends, funnel conversion and score distribution at a glance.',
  },
]

export default function Landing() {
  const { role } = useAuth()
  if (role) return <Navigate to={`/${role}`} replace />

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg">
      <div className="glow pointer-events-none absolute inset-0" />
      <header className="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Brand />
        <nav className="flex items-center gap-3">
          <Link to="/login" className={buttonClass('ghost')}>Sign in</Link>
          <Link to="/signup" className={buttonClass('primary')}>Get started</Link>
        </nav>
      </header>

      <main className="relative mx-auto max-w-6xl px-6 pb-24 pt-16 text-center sm:pt-24">
        <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/70 px-3 py-1 text-xs text-muted backdrop-blur">
          <Sparkles size={13} className="text-brand" /> Applicant tracking, powered by AI
        </span>
        <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold leading-tight tracking-tight text-ink sm:text-6xl">
          Hire the right people, <span className="text-gradient">faster</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted">
          Talent Scan reads resumes, ranks applicants by fit and gives your team a clear pipeline from first application to signed offer.
        </p>
        <div className="mt-9 flex flex-wrap justify-center gap-3">
          <Link to="/signup?as=company" className={buttonClass('primary')}>
            I am hiring <ArrowRight size={16} />
          </Link>
          <Link to="/signup?as=candidate" className={buttonClass('secondary')}>I am looking for a job</Link>
        </div>

        <div className="mt-24 grid gap-4 text-left sm:grid-cols-3">
          {features.map(({ icon: Icon, title, text }) => (
            <div key={title} className="rounded-xl border border-line bg-surface/80 p-6 backdrop-blur">
              <span className="mb-4 inline-flex rounded-lg bg-brand/15 p-2.5 text-brand">
                <Icon size={20} />
              </span>
              <h3 className="font-semibold text-ink">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{text}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
