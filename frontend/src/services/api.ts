// ── API client ─────────────────────────────────────────────────────
// Currently returns mock data. To connect the FastAPI backend later,
// set VITE_API_URL and replace the mock implementations in each service.

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function mockDelay<T>(data: T, ms = 100): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms));
}

export async function apiGet<T>(path: string): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error('API not configured — using mock data layer');
  }
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error('API not configured — using mock data layer');
  }
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}
