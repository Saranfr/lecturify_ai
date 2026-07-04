const API_BASE = '/api'

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('lecturify_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { error?: string }
    throw new Error(err?.error || res.statusText || 'Request failed')
  }
  return res.json()
}

export async function downloadFile(path: string, filename: string): Promise<void> {
  const token = localStorage.getItem('lecturify_token')
  const headers: HeadersInit = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { headers })
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export async function apiFormData(path: string, formData: FormData): Promise<unknown> {
  const token = localStorage.getItem('lecturify_token')
  const headers: HeadersInit = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
    headers,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || res.statusText || 'Request failed')
  }
  return res.json()
}
