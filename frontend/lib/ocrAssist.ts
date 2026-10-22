/**
 * Local interactive OCR assist API client (feature-branch / OCR_ASSIST_LOCAL).
 */

import {getApiUrl} from './config'
import {request} from './http'
import type {SpellCheckError} from './api'

export interface OcrAssistPageSummary {
  index: number
  status: 'final' | 'needs_review' | 'pending' | string
  attempt_count: number
  composite_score: number | null
  ocr_confidence?: number | null
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
  /** True when output.docx exists (accepted pages only; may be a partial job). */
  docx_ready: boolean
}

export interface VisionProviderResult {
  provider: string
  transcript: { text?: string; notes?: string | null } | null
  quality: Record<string, unknown> | null
  spellcheck_errors?: SpellCheckError[] | null
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
  latest_spellcheck_errors: SpellCheckError[] | null
  attempts: Array<{
    number: number
    ocr_text: string
    quality: Record<string, unknown> | null
    ai_verdict: Record<string, unknown> | null
    spellcheck_errors: SpellCheckError[] | null
  }>
  vision_by_provider: Record<
    string,
    {
      transcript: { text?: string; notes?: string | null }
      quality: Record<string, unknown> | null
      spellcheck_errors?: SpellCheckError[] | null
    }
  >
  image_url: string
}

export async function createOcrAssistJob(file: File): Promise<OcrAssistJob> {
  const form = new FormData()
  form.append('file', file)
  return request<OcrAssistJob>('/api/v1/ocr-assist/jobs', {
    method: 'POST',
    body: form,
  })
}

export async function getOcrAssistJob(jobId: string): Promise<OcrAssistJob> {
  return request<OcrAssistJob>(`/api/v1/ocr-assist/jobs/${jobId}`)
}

export async function getOcrAssistPage(
  jobId: string,
  pageIndex: number
): Promise<OcrAssistPageDetail> {
  return request<OcrAssistPageDetail>(
    `/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}`
  )
}

export async function postOcrAssistPageAction(
  jobId: string,
  pageIndex: number,
  body: {
    action: 'accept' | 'edit_accept' | 'retry' | 'compare_vision' | 'accept_vision'
    text?: string
    provider?: 'anthropic' | 'gemini'
    providers?: Array<'anthropic' | 'gemini'>
    /** Retry: enable TPS dewarp */
    use_tps?: boolean
    /** Retry: bake UI view orientation (degrees clockwise) into OCR settings */
    rotate?: number
  }
): Promise<{
  page: OcrAssistPageDetail
  compare?: { results: VisionProviderResult[] }
}> {
  const data = await request<
    OcrAssistPageDetail & {
      page?: OcrAssistPageDetail
      compare?: {results: VisionProviderResult[]}
    }
  >(`/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}/action`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  })
  // compare_vision returns { page, compare }; other actions return the page body.
  if (data.compare && data.page) {
    return {page: data.page, compare: data.compare}
  }
  return {page: data}
}

export function ocrAssistImageUrl(jobId: string, pageIndex: number): string {
  return `${getApiUrl()}/api/v1/ocr-assist/jobs/${jobId}/pages/${pageIndex}/image`
}

export function ocrAssistDocxUrl(jobId: string): string {
  return `${getApiUrl()}/api/v1/ocr-assist/jobs/${jobId}/docx`
}
