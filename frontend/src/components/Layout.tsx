import { useState } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import {
  Briefcase, FileText, LayoutDashboard, LogOut, Menu, PlusCircle, ScanSearch, Search, UserCircle, Users, X, type LucideIcon,
} from 'lucide-react'
import { useAuth } from '../auth'
import type { Role } from '../api'
import { cn } from '../lib'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end?: boolean
}

const nav: Record<Role, NavItem[]> = {
  candidate: [
    { to: '/candidate', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/candidate/jobs', label: 'Find jobs', icon: Search },
    { to: '/candidate/applications', label: 'My applications', icon: FileText },
    { to: '/candidate/profile', label: 'Profile', icon: UserCircle },
  ],
  company: [
    { to: '/company', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/company/jobs', label: 'Jobs', icon: Briefcase },
    { to: '/company/candidates', label: 'Candidates', icon: Users },
    { to: '/company/jobs/new', label: 'Post a job', icon: PlusCircle },
    { to: '/company/profile', label: 'Company', icon: UserCircle },
  ],
}

export function Brand() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white shadow-lg shadow-brand/30">
        <ScanSearch size={18} />
      </span>
      <span className="text-base font-semibold tracking-tight text-ink">Talent Scan</span>
    </Link>
  )
}

export default function Layout({ role }: { role: Role }) {
  const auth = useAuth()
  const [open, setOpen] = useState(false)
  const location = useLocation()

  if (auth.role !== role) return <Navigate to="/login" replace />

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="px-5 py-5">
        <Brand />
      </div>
      <p className="px-5 pb-2 text-[11px] font-semibold uppercase tracking-wider text-faint">
        {role === 'company' ? 'Recruiting' : 'Job search'}
      </p>
      <nav className="flex-1 space-y-1 px-3">
        {nav[role].map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
                isActive ? 'bg-brand/15 text-white' : 'text-muted hover:bg-raised hover:text-ink',
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={17} className={isActive ? 'text-brand' : ''} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-line p-3">
        <button
          onClick={auth.signOut}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted transition hover:bg-raised hover:text-ink"
        >
          <LogOut size={17} />
          Sign out
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-bg">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 border-r border-line bg-surface lg:block">{sidebar}</aside>

      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-surface/90 px-4 py-3 backdrop-blur lg:hidden">
        <Brand />
        <button onClick={() => setOpen(true)} className="rounded-lg p-2 text-muted hover:bg-raised" aria-label="Open menu">
          <Menu size={20} />
        </button>
      </header>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="drawer-enter absolute inset-y-0 left-0 w-64 border-r border-line bg-surface">
            <button onClick={() => setOpen(false)} className="absolute right-3 top-4 rounded-lg p-1.5 text-muted hover:bg-raised" aria-label="Close menu">
              <X size={18} />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <main className="lg:pl-60">
        <div key={location.pathname} className="mx-auto max-w-6xl px-4 py-8 sm:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
