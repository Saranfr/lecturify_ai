import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Lectures from './pages/Lectures'
import LectureDetail from './pages/LectureDetail'
import Quizzes from './pages/Quizzes'
import Analytics from './pages/Analytics'
import AdminDashboard from './pages/AdminDashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import { useAuth } from './hooks/useAuth'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function GuestOnly({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (token) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function StudentRedirect({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (user?.role === 'Student') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function FallbackRedirect() {
  const { token } = useAuth()
  return <Navigate to={token ? '/dashboard' : '/login'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
      <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="upload" element={<StudentRedirect><Upload /></StudentRedirect>} />
        <Route path="lectures" element={<Lectures />} />
        <Route path="lectures/:id" element={<LectureDetail />} />
        <Route path="quizzes" element={<Quizzes />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="admin" element={<AdminDashboard />} />
      </Route>
      <Route path="*" element={<FallbackRedirect />} />
    </Routes>
  )
}
