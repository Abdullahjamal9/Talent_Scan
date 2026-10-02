const TOKEN_KEY = 'ts_token'
const ROLE_KEY = 'ts_role'

export type Role = 'candidate' | 'company'

export const session = {
  get token() {
    return localStorage.getItem(TOKEN_KEY)
  },
  get role() {
    return localStorage.getItem(ROLE_KEY) as Role | null
  },
  /** The user id is stored inside the JWT payload. */
  get userId(): string {
    try {
      return JSON.parse(atob((this.token ?? '').split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).id
    } catch {
      return ''
    }
  },
  set(token: string, role: Role) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(ROLE_KEY, role)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ROLE_KEY)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function errorMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d?.msg === 'string' ? `${(d.loc ?? []).slice(1).join('.')} ${d.msg}`.trim() : String(d)))
      .join('; ')
  }
  return 'Request failed'
}

type Options = { method?: string; json?: unknown; form?: FormData }

export async function api<T = any>(path: string, { method, json, form }: Options = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (session.token) headers.Authorization = `Bearer ${session.token}`
  if (json !== undefined) headers['Content-Type'] = 'application/json'

  let res: Response
  try {
    res = await fetch(`/api/v1${path}`, {
      method: method ?? (json !== undefined || form ? 'POST' : 'GET'),
      headers,
      body: form ?? (json !== undefined ? JSON.stringify(json) : undefined),
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection.')
  }

  const body = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && session.token) {
      session.clear()
      window.location.assign('/login')
    }
    // No JSON body usually means the dev proxy could not reach the backend (it is not running)
    const fallback =
      res.status >= 500 && !body
        ? `The backend is not responding (HTTP ${res.status}). Make sure it is running on port 8000.`
        : `Request failed (HTTP ${res.status})`
    throw new ApiError(res.status, body?.detail ? errorMessage(body.detail) : fallback)
  }
  return body as T
}

// ---- Types (mirror the FastAPI schemas) ----

export interface Company {
  _id: string
  name?: string
  email?: string
  about?: string
  address?: string
  phone?: string
  totalEmployees?: number
  socials?: { linkedin?: string; facebook?: string; github?: string }
}

export interface Job {
  _id: string
  company: string | Company
  role?: string
  description?: string
  minimumSalary?: string
  maximumSalary?: string
  payingCurrency?: string
  jobType?: string
  isAcceptingApplications?: boolean
  genderRestriction?: GenderRestriction
  /** Only present for candidates: can this candidate apply given the job's gender setting? */
  eligibility?: 'ok' | 'gender_missing' | 'not_eligible'
  createdAt?: string
  matchScore?: number
  matchedSkills?: string[]
}

export type GenderRestriction = 'any' | 'female' | 'male'

export interface Analysis {
  summary?: string
  requirements?: { requirement: string; status: 'met' | 'partial' | 'missing' }[]
  strengths?: string[]
  gaps?: string[]
  /** Interview questions: recruiters only */
  questions?: string[]
  model?: string
  generatedAt?: string
}

export interface Experience {
  company_or_organization?: string
  role?: string
  startDate?: string
  endDate?: string
  description?: string
}

export interface Qualification {
  institute?: string
  program?: string
  startDate?: string
  endDate?: string
  description?: string
}

export interface Candidate {
  _id: string
  fullName?: string
  email: string
  about?: string
  bio?: string
  address?: string
  age?: string
  gender?: string
  phone?: string
  skills?: string[]
  resume?: string
  experience?: Experience[]
  qualification?: Qualification[]
  socials?: { linkedin?: string; facebook?: string; github?: string }
}

export type ApplicationStatus = 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'

export interface Application<J = string | Job, C = string | Company, K = string | Candidate> {
  _id: string
  job: J
  company: C
  candidate: K
  AIScore: number | null
  analysis?: Analysis | null
  status: ApplicationStatus
  notes?: string
  createdAt?: string
  updatedAt?: string
}

/** An application as returned to recruiters (candidate and job fully loaded). */
export type RecruiterApplication = Application<Job | string, string, Candidate>

export interface FunnelStep {
  stage: ApplicationStatus
  count: number
}

export interface CompanyDashboard {
  kpis: {
    openJobs: number
    totalJobs: number
    totalApplicants: number
    newThisWeek: number
    avgScore: number | null
    inInterview: number
    hired: number
  }
  funnel: FunnelStep[]
  trend: { date: string; count: number }[]
  scoreBuckets: { label: string; count: number }[]
  topCandidates: DashboardRow[]
  recent: DashboardRow[]
  jobs: {
    id: string
    role: string
    jobType?: string
    genderRestriction?: GenderRestriction
    createdAt?: string
    isAcceptingApplications: boolean
    applicants: number
    avgScore: number | null
  }[]
}

export interface DashboardRow {
  applicationId: string
  candidateId: string
  name: string
  email: string
  job: string
  jobId: string
  score: number | null
  status: ApplicationStatus
  createdAt: string
}

export interface CandidateDashboard {
  kpis: { applications: number; active: number; interviews: number; offers: number; avgScore: number | null }
  funnel: FunnelStep[]
  profile: { percent: number; missing: string[] }
  recent: {
    applicationId: string
    jobId: string
    role: string
    company: string
    status: ApplicationStatus
    score: number | null
    createdAt: string
    updatedAt: string
  }[]
  recommended: Job[]
}

export const JOB_TYPES = ['full time', 'part time', 'onsite', 'remote', 'hybrid', 'long term', 'contract']

export const asCompany = (c: Job['company']): Company | undefined => (typeof c === 'object' ? c : undefined)

/**
 * Resumes are private, so a plain link would be rejected (no auth header). Fetch the PDF with the token and show it
 * in a new tab. The tab is opened first, synchronously, so the browser does not treat it as a blocked popup.
 */
export async function openResume(candidateId: string) {
  const tab = window.open('', '_blank')
  try {
    const res = await fetch(`/api/v1/resume/${candidateId}`, { headers: { Authorization: `Bearer ${session.token}` } })
    if (!res.ok) throw new ApiError(res.status, 'Resume not available')
    const url = URL.createObjectURL(await res.blob())
    if (tab) tab.location.href = url
    else window.location.assign(url)
  } catch (e) {
    tab?.close()
    throw e
  }
}
