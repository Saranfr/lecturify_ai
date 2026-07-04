import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Activity } from 'lucide-react'

interface Overview {
  lectures_total: number
  lectures_by_status: Record<string, number>
  bloom_distribution: Record<string, number>
  total_mcqs: number
  dataset_info: Record<string, unknown>
}

interface Log {
  id: string
  event_type: string
  user_id?: string
  lecture_id?: string
  timestamp: string
  details?: Record<string, unknown>
}

const BLOOM_COLORS: Record<string, string> = {
  Remember: '#6366f1',
  Understand: '#8b5cf6',
  Apply: '#ec4899',
  Analyze: '#14b8a6',
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/60 ${className || ''}`} />
}

export default function Analytics() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api<Overview>('/analytics/overview'),
      api<Log[]>('/analytics/logs?limit=50'),
    ])
      .then(([o, l]) => {
        setOverview(o)
        setLogs(l)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div><Skeleton className="h-9 w-40" /><Skeleton className="h-5 w-64 mt-2" /></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  if (!overview) return <div className="card text-center py-16 text-red-600">Could not load analytics</div>

  const bloomData = Object.entries(overview.bloom_distribution).map(([name, value]) => ({ name, value }))
  const statusData = Object.entries(overview.lectures_by_status).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-primary-50">
          <Activity className="w-6 h-6 text-primary-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Analytics</h1>
          <p className="text-slate-500 mt-0.5">Topic coverage and Bloom level distribution</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-elevated">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Bloom Taxonomy Distribution</h2>
          {bloomData.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={bloomData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    innerRadius={50}
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
            <div className="h-48 flex items-center justify-center text-slate-400">No MCQ data yet</div>
          )}
        </div>
        <div className="card-elevated">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Lecture Processing Status</h2>
          {statusData.length ? (
            <div className="h-72">
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

      <div className="card-elevated">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity Logs</h2>
        <div className="space-y-1 max-h-80 overflow-y-auto">
          {logs.length === 0 ? (
            <p className="text-slate-500 py-4">No logs</p>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="flex flex-wrap gap-4 py-3 px-4 rounded-xl hover:bg-slate-50/80 border-b border-slate-50 last:border-0 text-sm"
              >
                <span className="font-mono text-primary-600 font-medium">{log.event_type}</span>
                <span className="text-slate-500">{log.timestamp}</span>
                {log.lecture_id && <span className="text-slate-600">Lecture: {log.lecture_id.slice(0, 8)}...</span>}
                {log.details && Object.keys(log.details).length > 0 && (
                  <span className="text-slate-500">{JSON.stringify(log.details)}</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
