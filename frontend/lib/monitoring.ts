/**
 * Error reporting to Sentry.
 *
 * Off unless NEXT_PUBLIC_SENTRY_DSN is set at build time, so local dev,
 * tests and preview builds send nothing. Only API failures users actually
 * hit are reported (network errors, timeouts, 5xx) — never request bodies,
 * since those carry the user's text or PDF.
 */
import * as Sentry from '@sentry/browser'

let enabled = false

export function initMonitoring(): void {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN?.trim()
  if (enabled || !dsn || typeof window === 'undefined') return
  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV,
    tracesSampleRate: 0,
  })
  enabled = true
}

export type ApiFailureKind = 'timeout' | 'network' | 'server'

export function reportApiFailure(
  path: string,
  kind: ApiFailureKind,
  error: Error,
  status?: number
): void {
  if (!enabled) return
  Sentry.captureException(error, {
    tags: {api_path: path, api_failure: kind, status: String(status ?? 0)},
  })
}
