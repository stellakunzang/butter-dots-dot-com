/**
 * API client for Tibetan Spell Checker backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SpellCheckError {
  word: string
  position: number
  error_type: string
  severity: string
  message?: string
  component?: string
}

export interface SpellCheckResponse {
  text: string
  error_count: number
  errors: SpellCheckError[]
}

export interface SpellCheckRequest {
  text: string
}

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

/**
 * Check Tibetan text for spelling errors
 * @param text Tibetan text to check
 * @returns Spell check results with errors
 * @throws APIError if request fails
 */
export async function checkText(text: string): Promise<SpellCheckResponse> {
  if (!text || text.trim().length === 0) {
    throw new APIError('Text cannot be empty', 400)
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/spellcheck/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text } as SpellCheckRequest),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new APIError(
        errorData?.detail || `Request failed with status ${response.status}`,
        response.status,
        errorData
      )
    }

    const data: SpellCheckResponse = await response.json()
    return data
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }

    // Network or other errors
    if (error instanceof TypeError) {
      throw new APIError(
        'Unable to connect to spell checker service. Please make sure the backend is running.',
        0
      )
    }

    throw new APIError(
      error instanceof Error ? error.message : 'An unexpected error occurred',
      0
    )
  }
}

/**
 * Check if the API is reachable
 * @returns true if API is healthy
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
    })
    return response.ok
  } catch {
    return false
  }
}
