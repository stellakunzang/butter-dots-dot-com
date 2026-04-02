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

// ---------------------------------------------------------------------------
// PDF upload types and functions
// ---------------------------------------------------------------------------

export interface PDFSpellError {
  word: string
  page: number
  error_type: string
  severity: string
  message?: string
  component?: string
}

export interface PDFResultURLs {
  pdf: string
  docx: string
}

export interface PDFUploadSyncResponse {
  job_id: string
  page_count: number
  error_count: number
  errors: PDFSpellError[]
  is_scanned: boolean
  pdf_url: string
  docx_url: string
}

export interface PDFUploadAsyncResponse {
  job_id: string
  page_count: number
  status: 'pending'
  message: string
}

export type PDFUploadResponse = PDFUploadSyncResponse | PDFUploadAsyncResponse

export function isSyncResponse(r: PDFUploadResponse): r is PDFUploadSyncResponse {
  return 'errors' in r
}

export type JobStatusType = 'pending' | 'processing' | 'completed' | 'failed'

export interface JobStatusResponse {
  job_id: string
  status: JobStatusType
  progress: number
  page_count: number
  error_count?: number
  error_message?: string
  pdf_url?: string
  docx_url?: string
}

/**
 * Upload a PDF for OCR and spell checking.
 * Small PDFs (≤15 pages) return results immediately.
 * Large PDFs return a job_id for polling.
 */
export async function uploadPDF(
  file: File,
  email?: string
): Promise<PDFUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (email) {
    formData.append('email', email)
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/spellcheck/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new APIError(
        errorData?.detail || `Upload failed with status ${response.status}`,
        response.status,
        errorData
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof APIError) throw error
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
 * Poll the status of an async PDF processing job.
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_URL}/api/v1/spellcheck/job/${jobId}`)
  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new APIError(
      errorData?.detail || `Status check failed with status ${response.status}`,
      response.status,
      errorData
    )
  }
  return response.json()
}

/**
 * Get the absolute download URLs for a completed job.
 */
export function getResultURLs(jobId: string): PDFResultURLs {
  return {
    pdf: `${API_URL}/api/v1/spellcheck/result/${jobId}/pdf`,
    docx: `${API_URL}/api/v1/spellcheck/result/${jobId}/docx`,
  }
}
