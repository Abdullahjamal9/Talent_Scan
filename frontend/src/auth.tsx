import { createContext, useContext, useState, type ReactNode } from 'react'
import { api, session, type Role } from './api'

interface AuthState {
  role: Role | null
  signIn: (role: Role, email: string, password: string) => Promise<void>
  signUpCandidate: (form: FormData) => Promise<{ resumeParsed: boolean }>
  signUpCompany: (data: { name: string; email: string; password: string }) => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role | null>(session.role)

  const finish = (token: string, r: Role) => {
    session.set(token, r)
    setRole(r)
  }

  const value: AuthState = {
    role,
    async signIn(r, email, password) {
      const res = await api(`/${r}/sign-in`, { json: { email, password } })
      finish(res.data.token, r)
    },
    async signUpCandidate(form) {
      const res = await api('/candidate/sign-up', { form })
      finish(res.token, 'candidate')
      return { resumeParsed: res.resumeParsed }
    },
    async signUpCompany(data) {
      await api('/company/sign-up', { json: data })
      const res = await api('/company/sign-in', { json: { email: data.email, password: data.password } })
      finish(res.data.token, 'company')
    },
    signOut() {
      session.clear()
      setRole(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
