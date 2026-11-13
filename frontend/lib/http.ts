import {getApiUrl} from './config'
import {reportApiFailure} from './monitoring'

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'APIError'
  }
}

const NETWORK_MESSAGE =
  'Unable to connect to spell checker service. Please make sure the backend is running.'

const TIMEOUT_MESSAGE =
  'The spell checker service did not respond in time. Please try again in a few minutes.'

/** How long a request may wait before it is abandoned and reported. */
export const DEFAULT_TIMEOUT_MS = 60_000
/** Page OCR and AI comparisons run inside the request. */
export const LONG_TIMEOUT_MS = 5 * 60_000
/** PDF uploads are processed inside the request; a long scanned book takes minutes. */
export const UPLOAD_TIMEOUT_MS = 15 * 60_000

export async function parseError(
  response: Response,
  fallback?: string
): Promise<APIError> {
  const errorData = await response.json().catch(() => null)
  const detail =
    errorData && typeof errorData === 'object' && 'detail' in errorData
      ? (errorData as {detail?: unknown}).detail
      : undefined
  const message =
    typeof detail === 'string'
      ? detail
      : fallback
        ? `${fallback} ${response.status}`
        : `Request failed with status ${response.status}`
  return new APIError(message, response.status, errorData)
}

export async function request<T>(
  path: string,
  init?: RequestInit,
  fallback?: string,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(`${getApiUrl()}${path}`, {...init, signal: controller.signal})
  } catch (error) {
    if (error instanceof APIError) throw error
    if (controller.signal.aborted) {
      const timeout = new APIError(TIMEOUT_MESSAGE, 0)
      reportApiFailure(path, 'timeout', timeout)
      throw timeout
    }
    if (error instanceof TypeError) {
      const network = new APIError(NETWORK_MESSAGE, 0)
      reportApiFailure(path, 'network', network)
      throw network
    }
    throw new APIError(
      error instanceof Error ? error.message : 'An unexpected error occurred',
      0
    )
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    const failure = await parseError(response, fallback)
    if (response.status >= 500) {
      reportApiFailure(path, 'server', failure, response.status)
    }
    throw failure
  }
  return response.json() as Promise<T>
}
