import { createContext, useContext, useState, ReactNode } from 'react'

interface User {
  email: string
  role: string
  name: string
}

interface AuthContextType {
  token: string | null
  user: User | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string, role?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

const STORAGE_KEY = 'lecturify_token'
const USER_KEY = 'lecturify_user'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState<User | null>(() => {
    const u = localStorage.getItem(USER_KEY)
    return u ? JSON.parse(u) : null
  })

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || 'Login failed')
    }
    const data = await res.json()
    setToken(data.token)
    setUser(data.user)
    localStorage.setItem(STORAGE_KEY, data.token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  }

  const register = async (email: string, password: string, name?: string, role?: string) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name, role }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || 'Registration failed')
    }
    await login(email, password)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
