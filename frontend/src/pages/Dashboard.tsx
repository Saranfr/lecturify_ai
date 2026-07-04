import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { Upload, List, BarChart3, FileText, CheckCircle, Sparkles } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface Overview {
  lectures_total: number
  lectures_by_status: Record<string, number>
  bloom_distribution: Record<string, number>
  total_mcqs: number
  dataset_info: { training_available: boolean; mcq_samples: number; bloom_samples: number }
  difficulty_filter?: string
}

const BLOOM_COLORS: Record<string, string> = {
  Remember: '#6366f1',
  Understand: '#8b5cf6',
  Apply: '#ec4899',
  Analyze: '#14b8a6',
}

const STAT_CARDS = [
  { key: 'lectures', label: 'Total Lectures', icon: FileText, bg: 'bg-primary-50', iconColor: 'text-primary-600' },
  { key: 'mcqs', label: 'Total MCQs', icon: CheckCircle, bg: 'bg-emerald-50', iconColor: 'text-emerald-600' },
  { key: 'training', label: 'Training Data', icon: BarChart3, bg: 'bg-slate-100', iconColor: 'text-slate-600' },
]

const DIFFICULTY_COLORS: Record<string, string> = {
  All: 'bg-slate-200 text-slate-800',
  Easy: 'bg-emerald-100 text-emerald-800',
  Medium: 'bg-amber-100 text-amber-800',
  Hard: 'bg-rose-100 text-rose-800',
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/70 ${className || ''}`} />
}

export default function Dashboard() {
  const { user } = useAuth()
  const [overview, setOverview] = useState<Overview | null>(null)
  const isStudent = user?.role === 'Student'
  const [loading, setLoading] = useState(true)
  const [difficultyFilter, setDifficultyFilter] = useState<'All' | 'Easy' | 'Medium' | 'Hard'>('All')

  useEffect(() => {
    setLoading(true)
    const url = difficultyFilter === 'All'
      ? '/analytics/overview'
      : `/analytics/overview?difficulty=${difficultyFilter}`
    api<Overview>(url)
      .then(setOverview)
      .catch(() => setOverview(null))
      .finally(() => setLoading(false))
  }, [difficultyFilter])

  if (loading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-80" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="card text-center py-16">
        <p className="text-red-600 text-lg">Could not load dashboard</p>
        <p className="text-slate-500 mt-2">Check that the backend is running.</p>
      </div>
    )
  }

  const bloomData = Object.entries(overview.bloom_distribution).map(([name, value]) => ({ name, value }))
  const statusData = Object.entries(overview.lectures_by_status).map(([name, value]) => ({ name, value }))

  const statValues = {
    lectures: overview.lectures_total,
    mcqs: overview.total_mcqs,
    training: overview.dataset_info.training_available ? 'Available' : 'Not found',
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dashboard</h1>
          <p className="text-slate-500 mt-1">Overview of lecture processing and MCQ generation</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-500">Filter:</span>
          {(['All', 'Easy', 'Medium', 'Hard'] as const).map((level) => (
            <button
              key={level}
              onClick={() => setDifficultyFilter(level)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                difficultyFilter === level ? DIFFICULTY_COLORS[level] : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {STAT_CARDS.map(({ key, label, icon: Icon, bg, iconColor }) => (
          <div key={key} className="card group hover:shadow-glow transition-shadow">
            <div className="flex items-start justify-between">
              <div className={`p-3 rounded-xl ${bg}`}>
                <Icon className={`w-6 h-6 ${iconColor}`} />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-4">{label}</p>
            <p className="text-2xl font-bold text-slate-900 mt-0.5">
              {typeof statValues[key as keyof typeof statValues] === 'number'
                ? statValues[key as keyof typeof statValues]
                : String(statValues[key as keyof typeof statValues])}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-elevated">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Bloom Taxonomy Distribution</h2>
          {bloomData.length ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={bloomData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={85}
                    innerRadius={45}
                    paddingAngle={2}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {bloomData.map((_, i) => (
                      <Cell key={i} fill={BLOOM_COLORS[bloomData[i].name] || '#94a3b8'} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400">
              <Sparkles className="w-12 h-12 opacity-50" />
              <span className="ml-2">No MCQ data yet</span>
            </div>
          )}
        </div>
        <div className="card-elevated">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Lecture Status</h2>
          {statusData.length ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400">No lectures yet</div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 pt-2">
        {!isStudent && (
          <Link to="/upload" className="btn-primary inline-flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Lecture
          </Link>
        )}
        <Link to={isStudent ? '/quizzes' : '/lectures'} className="btn-secondary inline-flex items-center gap-2">
          <List className="w-5 h-5" />
          {isStudent ? 'View Quizzes' : 'View Lectures'}
        </Link>
        {!isStudent && (
          <Link to="/analytics" className="btn-secondary inline-flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Analytics
          </Link>
        )}
      </div>
    </div>
  )
}
