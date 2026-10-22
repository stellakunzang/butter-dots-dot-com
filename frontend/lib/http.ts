import {getApiUrl} from './config'

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
  fallback?: string
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${getApiUrl()}${path}`, init)
  } catch (error) {
    if (error instanceof APIError) throw error
    if (error instanceof TypeError) {
      throw new APIError(NETWORK_MESSAGE, 0)
    }
    throw new APIError(
      error instanceof Error ? error.message : 'An unexpected error occurred',
      0
    )
  }

  if (!response.ok) {
    throw await parseError(response, fallback)
  }
  return response.json() as Promise<T>
}
