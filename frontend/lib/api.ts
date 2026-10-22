/**
 * API client for Tibetan Spell Checker backend
 */

import {getApiUrl} from './config'
import {APIError, request} from './http'

export {APIError}

export interface SpellCheckError {
  word: string
  position: number
  error_type: string
  severity: string
  message?: string
  component?: string
  corpus_hit?: boolean | null
}

export interface SpellCheckResponse {
  text: string
  error_count: number
  errors: SpellCheckError[]
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

  return request<SpellCheckResponse>('/api/v1/spellcheck/text', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  })
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
  corpus_hit?: boolean | null
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

  return request<PDFUploadResponse>(
    '/api/v1/spellcheck/upload',
    {method: 'POST', body: formData},
    'Upload failed with status'
  )
}

/**
 * Poll the status of an async PDF processing job.
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(
    `/api/v1/spellcheck/job/${jobId}`,
    undefined,
    'Status check failed with status'
  )
}

export function getResultURLs(jobId: string) {
  const apiUrl = getApiUrl()
  return {
    pdf: `${apiUrl}/api/v1/spellcheck/result/${jobId}/pdf`,
    docx: `${apiUrl}/api/v1/spellcheck/result/${jobId}/docx`,
  }
}
