import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { FileText, CheckCircle, Play } from 'lucide-react'

interface Lecture {
  id: string
  filename: string
  file_type: string
  status: string
  mcqs?: unknown[]
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/60 ${className || ''}`} />
}

export default function Quizzes() {
  const [lectures, setLectures] = useState<Lecture[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api<Lecture[]>('/lecture/lectures')
      .then((list) => setLectures(list.filter((l) => l.status === 'processed' && (l.mcqs?.length ?? 0) > 0)))
      .catch(() => setLectures([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div><Skeleton className="h-9 w-40" /><Skeleton className="h-5 w-72 mt-2" /></div>
        <div className="grid gap-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Quizzes</h1>
        <p className="text-slate-500 mt-1">Practice with MCQs generated from lecture content</p>
      </div>

      <div className="grid gap-3">
        {lectures.length === 0 ? (
          <div className="card text-center py-16">
            <CheckCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">No quizzes available yet.</p>
            <p className="text-sm text-slate-400 mt-1">Check back when your instructor adds lecture content.</p>
          </div>
        ) : (
          lectures.map((l) => (
            <Link
              key={l.id}
              to={`/lectures/${l.id}`}
              className="card flex items-center gap-4 group hover:shadow-glow hover:border-primary-200/60 transition-all"
            >
              <div className="p-3 rounded-xl bg-gradient-to-br from-primary-50 to-primary-100/50 shrink-0">
                <FileText className="w-8 h-8 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-800 truncate group-hover:text-primary-600 transition-colors">
                  {l.filename}
                </p>
                <p className="text-sm text-slate-500 mt-0.5">
                  {l.mcqs?.length ?? 0} questions • Click to start
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-primary-100 text-primary-600 group-hover:bg-primary-200/80 transition-colors shrink-0">
                <Play className="w-5 h-5" />
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
