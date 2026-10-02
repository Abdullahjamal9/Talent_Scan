import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth'
import Layout from './components/Layout'
import { PageSkeleton } from './components/ui'
import Landing from './pages/Landing'
import { Login, SignUp } from './pages/Auth'
const CandidateDashboard = lazy(() => import('./pages/candidate/Dashboard'))
const Jobs = lazy(() => import('./pages/candidate/Jobs'))
const JobDetail = lazy(() => import('./pages/candidate/JobDetail'))
const MyApplications = lazy(() => import('./pages/candidate/MyApplications'))
const CandidateProfile = lazy(() => import('./pages/candidate/Profile'))
const CompanyDashboard = lazy(() => import('./pages/company/Dashboard'))
const CompanyJobs = lazy(() => import('./pages/company/Jobs'))
const JobForm = lazy(() => import('./pages/company/JobForm'))
const Pipeline = lazy(() => import('./pages/company/Pipeline'))
const Candidates = lazy(() => import('./pages/company/Candidates'))
const CompanyProfile = lazy(() => import('./pages/company/Profile'))

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />

          <Route path="/candidate" element={<Layout role="candidate" />}>
            <Route index element={<CandidateDashboard />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/:id" element={<JobDetail />} />
            <Route path="applications" element={<MyApplications />} />
            <Route path="profile" element={<CandidateProfile />} />
          </Route>

          <Route path="/company" element={<Layout role="company" />}>
            <Route index element={<CompanyDashboard />} />
            <Route path="jobs" element={<CompanyJobs />} />
            <Route path="jobs/new" element={<JobForm />} />
            <Route path="jobs/:id/edit" element={<JobForm />} />
            <Route path="jobs/:id/pipeline" element={<Pipeline />} />
            <Route path="candidates" element={<Candidates />} />
            <Route path="profile" element={<CompanyProfile />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  )
}
