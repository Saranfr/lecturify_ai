import { useState, useRef, useEffect } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useNotifications } from '../hooks/useNotifications'
import { BookOpen, Upload, List, BarChart3, Shield, LogOut, Bell, ClipboardList, Menu, X } from 'lucide-react'

export default function Layout() {
  const { token, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { notifications, unreadCount, markAsRead } = useNotifications()
  const [notifOpen, setNotifOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false)
    }
    document.addEventListener('click', h)
    return () => document.removeEventListener('click', h)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isStudent = user?.role === 'Student'
  const nav = [
    { to: '/dashboard', label: 'Dashboard', icon: BookOpen },
    ...(isStudent
      ? [{ to: '/quizzes', label: 'Quizzes', icon: ClipboardList }]
      : [
          { to: '/upload', label: 'Upload', icon: Upload },
          { to: '/lectures', label: 'Lectures', icon: List },
          { to: '/analytics', label: 'Analytics', icon: BarChart3 },
        ]),
  ]
  if (user?.role === 'Admin') nav.push({ to: '/admin', label: 'Admin', icon: Shield })

  return (
    <div className="min-h-screen flex bg-surface-50">
      {/* Sidebar - desktop (dark) */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-surface-900 border-r border-surface-800">
        <div className="flex items-center gap-3 px-5 py-5 border-b border-surface-800">
          <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg text-white">Lecturify AI</span>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || (to !== '/dashboard' && location.pathname.startsWith(to))
            return (
              <Link
                key={to}
                to={to}
                className={active ? 'nav-link-active' : 'nav-link'}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {label}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40 animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`lg:hidden fixed top-0 left-0 z-50 h-full w-64 bg-surface-900 border-r border-surface-800 shadow-2xl transform transition-transform duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-surface-800">
          <div className="flex items-center gap-2">
            <BookOpen className="w-8 h-8 text-primary-400" />
            <span className="font-bold text-white">Lecturify AI</span>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="p-2 rounded-lg hover:bg-surface-800 text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="p-3 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={location.pathname === to || (to !== '/dashboard' && location.pathname.startsWith(to)) ? 'nav-link-active' : 'nav-link'}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-lg border-b border-slate-200/80">
          <div className="flex items-center justify-between px-4 lg:px-8 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 -ml-2 rounded-xl hover:bg-slate-100 text-slate-600"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex-1" />
            {token && (
              <div className="flex items-center gap-2">
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setNotifOpen((o) => !o)}
                    className="relative p-2.5 rounded-xl hover:bg-slate-100 text-slate-600 transition-colors"
                    title="Notifications"
                  >
                    <Bell className="w-5 h-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary-500 text-[10px] font-bold text-white ring-2 ring-white">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>
                  {notifOpen && (
                    <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-auto bg-white rounded-2xl shadow-card-hover border border-slate-200 animate-slide-up z-50">
                      <div className="p-4 border-b border-slate-100 font-semibold text-slate-800">Notifications</div>
                      {notifications.length === 0 ? (
                        <div className="p-6 text-slate-400 text-sm text-center">No notifications</div>
                      ) : (
                        notifications.map((n) => (
                          <Link
                            key={n.id}
                            to={n.link || '#'}
                            onClick={() => {
                              markAsRead(n.id)
                              setNotifOpen(false)
                            }}
                            className={`block p-4 border-b border-slate-50 last:border-0 hover:bg-slate-50/80 transition-colors ${!n.read ? 'bg-primary-50/40' : ''}`}
                          >
                            <div className="font-medium text-slate-800">{n.title}</div>
                            <div className="text-sm text-slate-500 truncate mt-0.5">{n.message}</div>
                            <div className="text-xs text-slate-400 mt-2">
                              {new Date(n.created_at).toLocaleDateString()}
                            </div>
                          </Link>
                        ))
                      )}
                    </div>
                  )}
                </div>
                <div className="hidden sm:flex items-center gap-2 pl-3 ml-2 border-l border-slate-200">
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-sm font-semibold">
                    {(user?.name || user?.email || 'U')[0].toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-slate-700 max-w-[120px] truncate">{user?.name || user?.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2.5 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
