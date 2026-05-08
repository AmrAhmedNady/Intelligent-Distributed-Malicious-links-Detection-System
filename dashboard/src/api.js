// api.js — NovaShield API client
// Uses relative URLs so Vite proxy handles CORS (see vite.config.js)
const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health:       () => request('/health'),
  stats:        () => request('/api/stats'),
  results:      (limit = 200) => request(`/api/results?limit=${limit}`),
  logs:         (limit = 300) => request(`/api/logs?limit=${limit}`),
  systemStatus: () => request('/api/system-status'),
  clearResults: () => request('/api/results', { method: 'DELETE' }),
  scanDirect:   (urls) => request('/api/scan/direct', {
    method: 'POST',
    body: JSON.stringify({ urls }),
  }),
  scanDistributed: (urls) => request('/api/scan', {
    method: 'POST',
    body: JSON.stringify({ urls }),
  }),
}
