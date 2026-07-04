import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api } from '../api/client'

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  link?: string
  lecture_id?: string
  read: boolean
  created_at: string
}

interface NotificationsContextType {
  notifications: Notification[]
  unreadCount: number
  refresh: () => void
  markAsRead: (id: string) => void
}

const NotificationsContext = createContext<NotificationsContextType | null>(null)

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const refresh = useCallback(() => {
    api<Notification[]>('/notifications?limit=20')
      .then((list) => {
        setNotifications(list)
        setUnreadCount(list.filter((n) => !n.read).length)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 30_000)
    return () => clearInterval(interval)
  }, [refresh])

  const markAsRead = useCallback(
    (id: string) => {
      api(`/notifications/${id}/read`, { method: 'POST' }).catch(() => {})
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
      setUnreadCount((c) => Math.max(0, c - 1))
    },
    []
  )

  return (
    <NotificationsContext.Provider
      value={{ notifications, unreadCount, refresh, markAsRead }}
    >
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  return ctx ?? { notifications: [], unreadCount: 0, refresh: () => {}, markAsRead: () => {} }
}
