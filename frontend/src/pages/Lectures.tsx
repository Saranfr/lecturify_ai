import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { FileText, Clock, CheckCircle, XCircle, Trash2 } from 'lucide-react'

interface Lecture {
  id: string
  filename: string
  file_type: string
  status: string
  created_at: string
  mcqs?: unknown[]
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/60 ${className || ''}`} />
}

export default function Lectures() {
  const [lectures, setLectures] = useState<Lecture[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchLectures = () => {
    api<Lecture[]>('/lecture/lectures')
      .then(setLectures)
      .catch(() => setLectures([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setLoading(true)
    fetchLectures()
  }, [])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Delete this lecture? This cannot be undone.')) return
    setDeletingId(id)
    try {
      await api(`/lecture/lectures/${id}`, { method: 'DELETE' })
      setLectures((prev) => prev.filter((l) => l.id !== id))
    } catch {
      alert('Failed to delete lecture')
    } finally {
      setDeletingId(null)
    }
  }

  const statusIcon = (s: string) => {
    if (s === 'processed') return <CheckCircle className="w-5 h-5 text-emerald-500" />
    if (s === 'failed') return <XCircle className="w-5 h-5 text-rose-500" />
    return <Clock className="w-5 h-5 text-amber-500" />
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div><Skeleton className="h-9 w-40" /><Skeleton className="h-5 w-64 mt-2" /></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Lectures</h1>
          <p className="text-slate-500 mt-1">View and manage your uploaded lectures</p>
        </div>
      </div>

      <div className="grid gap-3">
        {lectures.length === 0 ? (
          <div className="card text-center py-16">
            <p className="text-slate-500">No lectures yet.</p>
            <Link to="/upload" className="btn-primary inline-flex items-center gap-2 mt-4">
              Upload one
            </Link>
          </div>
        ) : (
          lectures.map((l) => (
            <div
              key={l.id}
              className="card flex items-center justify-between group hover:shadow-glow transition-all"
            >
              <Link to={`/lectures/${l.id}`} className="flex-1 flex items-center gap-4 min-w-0">
                <div className="p-3 rounded-xl bg-primary-50 shrink-0">
                  <FileText className="w-8 h-8 text-primary-600" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-slate-800 truncate group-hover:text-primary-600 transition-colors">
                    {l.filename}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {l.file_type} • {new Date(l.created_at).toLocaleDateString()}
                  </p>
                </div>
              </Link>
              <div className="flex items-center gap-3 shrink-0">
                {statusIcon(l.status)}
                <span className="text-sm font-medium capitalize text-slate-600">{l.status}</span>
                {l.mcqs && l.mcqs.length > 0 && (
                  <span className="text-sm text-slate-400">• {l.mcqs.length} MCQs</span>
                )}
                <button
                  onClick={(e) => handleDelete(e, l.id)}
                  disabled={deletingId === l.id}
                  className="p-2.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  title="Delete lecture"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
