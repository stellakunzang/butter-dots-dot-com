/**
 * Backend origin for browser requests.
 *
 * Development falls back to localhost. A production build with no
 * NEXT_PUBLIC_API_URL fails on the first request instead of silently
 * calling the wrong host.
 */
export function getApiUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim()
  if (configured) {
    return configured.replace(/\/$/, '')
  }
  if (process.env.NODE_ENV === 'production') {
    throw new Error('NEXT_PUBLIC_API_URL is not set')
  }
  return 'http://localhost:8000'
}
