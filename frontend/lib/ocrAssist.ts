/**
 * Local interactive OCR assist API client (feature-branch / OCR_ASSIST_LOCAL).
 */

import { APIError } from './api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface OcrAssistPageSummary {
  index: number
  status: 'final' | 'needs_review' | 'pending' | string
  attempt_count: number
  composite_score: number | null
  has_vision_compare: boolean
}

export interface OcrAssistJob {
  id: string
  source_file: string
  page_count: number
  status: string
  running: boolean
  created_at: string
  pages: OcrAssistPageSummary[]
  docx_ready: boolean
}

export interface VisionProviderResult {
  provider: string
  transcript: { text?: string; notes?: string | null } | null
  quality: Record<string, unknown> | null
  composite_score: number | null
  decision: string | null
  error: string | null
}

export interface OcrAssistPageDetail {
  index: number
  status: string
  settings: Record<string, unknown>
  final_text: string | null
  final_quality: Record<string, unknown> | null
  notes: string | null
  latest_ocr_text: string | null
  latest_quality: Record<string, unknown> | null
  attempts: Array<{
    number: number
    ocr_text: string
    quality: Record<string, unknown> | null
    ai_verdict: Record<string, unknown> | null
  }>
  vision_by_provider: Record<
    string,
    { transcript: { text?: string; notes?: string | null }; quality: Record<string, unknown> | null }
  >
  image_url: string
}

async function parseError(response: Response): Promise<APIError> {
  const errorData = await response.json().catch(() => null)
  const detail = errorData?.detail
  const message =
    typeof detail === 'string'
      ? detail
      : `Request failed with status ${response.status}`
  return new APIError(message, response.status, errorData)
}

export async function createOcrAssistJob(file: File): Promise<OcrAssistJob> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`${API_URL}/api/v1/ocr-assist/jobs`, {
    method: 'POST',
    body: form,
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function getOcrAssistJob(jobId: string): Promise<OcrAssistJob> {
  const response = await fetch(`${API_URL}/api/v1/ocr-assist/jobs/${jobId}`)
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function getOcrAssistPage(
  jobId: string,
  pageIndex: number
): Promise<OcrAssistPageDetail> {
  const response = await fetch(
    `${API_URL}/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}`
  )
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function postOcrAssistPageAction(
  jobId: string,
  pageIndex: number,
  body: {
    action: 'accept' | 'edit_accept' | 'retry' | 'compare_vision' | 'accept_vision'
    text?: string
    provider?: 'anthropic' | 'gemini'
  }
): Promise<{
  page: OcrAssistPageDetail
  compare?: { results: VisionProviderResult[] }
}> {
  const response = await fetch(
    `${API_URL}/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}/action`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }
  )
  if (!response.ok) throw await parseError(response)
  const data = await response.json()
  // compare_vision returns { page, compare }; other actions return the page body.
  if (data.compare) {
    return data
  }
  return { page: data }
}

export function ocrAssistImageUrl(jobId: string, pageIndex: number): string {
  return `${API_URL}/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}/image`
}

export function ocrAssistDocxUrl(jobId: string): string {
  return `${API_URL}/api/v1/ocr-assist/jobs/${jobId}/docx`
}
