import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { FileText, CheckCircle, Database, Shield } from 'lucide-react'

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

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/60 ${className || ''}`} />
}

export default function AdminDashboard() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [logs, setLogs] = useState<Log[]>([])

  useEffect(() => {
    Promise.all([
      api<Overview>('/analytics/overview'),
      api<Log[]>('/analytics/logs?limit=100'),
    ])
      .then(([o, l]) => {
        setOverview(o)
        setLogs(l)
      })
      .catch(() => {})
  }, [])

  if (!overview) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div><Skeleton className="h-9 w-48" /><Skeleton className="h-5 w-72 mt-2" /></div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  const statusData = Object.entries(overview.lectures_by_status).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-slate-100">
          <Shield className="w-6 h-6 text-slate-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Admin Dashboard</h1>
          <p className="text-slate-500 mt-0.5">System-wide analytics and audit logs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary-50">
              <FileText className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total Lectures</p>
              <p className="text-xl font-bold text-slate-800">{overview.lectures_total}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-50">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total MCQs</p>
              <p className="text-xl font-bold text-slate-800">{overview.total_mcqs}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-slate-100">
              <Database className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Training Data</p>
              <p className="text-lg font-bold text-slate-800">
                {(overview.dataset_info as { training_available?: boolean }).training_available ? 'Available' : 'Not found'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card-elevated">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Lecture Status Distribution</h2>
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
          <p className="text-slate-500">No data</p>
        )}
      </div>

      <div className="card-elevated">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Audit Logs</h2>
        <div className="overflow-x-auto max-h-96 overflow-y-auto rounded-xl border border-slate-100">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/80">
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Event</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">User</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Lecture</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Time</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-mono text-primary-600">{log.event_type}</td>
                  <td className="py-3 px-4 text-slate-600">{log.user_id || '-'}</td>
                  <td className="py-3 px-4 text-slate-600">{log.lecture_id ? log.lecture_id.slice(0, 8) + '...' : '-'}</td>
                  <td className="py-3 px-4 text-slate-500">{log.timestamp}</td>
                  <td className="py-3 px-4 text-slate-500">{log.details ? JSON.stringify(log.details) : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
