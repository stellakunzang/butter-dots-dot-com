/**
 * Local interactive OCR QA UI (feat/interactive-ocr only).
 * Requires backend OCR_ASSIST_LOCAL=true. Not linked from main nav.
 */
import React, { useCallback, useEffect, useState } from 'react'
import { Layout, PageTitle } from '@/components'
import { APIError } from '@/lib/api'
import {
  OcrAssistJob,
  OcrAssistPageDetail,
  VisionProviderResult,
  createOcrAssistJob,
  getOcrAssistJob,
  getOcrAssistPage,
  ocrAssistDocxUrl,
  ocrAssistImageUrl,
  postOcrAssistPageAction,
} from '@/lib/ocrAssist'

export default function OcrAssistPage() {
  const [job, setJob] = useState<OcrAssistJob | null>(null)
  const [selectedPage, setSelectedPage] = useState<number | null>(null)
  const [pageDetail, setPageDetail] = useState<OcrAssistPageDetail | null>(null)
  const [editText, setEditText] = useState('')
  const [compareResults, setCompareResults] = useState<VisionProviderResult[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshJob = useCallback(async (jobId: string) => {
    const next = await getOcrAssistJob(jobId)
    setJob(next)
    return next
  }, [])

  const loadPage = useCallback(async (jobId: string, pageIndex: number) => {
    const detail = await getOcrAssistPage(jobId, pageIndex)
    setPageDetail(detail)
    setEditText(detail.final_text ?? detail.latest_ocr_text ?? '')
    if (detail.vision_by_provider && Object.keys(detail.vision_by_provider).length > 0) {
      setCompareResults(
        Object.entries(detail.vision_by_provider).map(([provider, entry]) => ({
          provider,
          transcript: entry.transcript,
          quality: entry.quality,
          composite_score:
            typeof entry.quality?.composite_score === 'number'
              ? (entry.quality.composite_score as number)
              : null,
          decision: null,
          error: null,
        }))
      )
    }
  }, [])

  useEffect(() => {
    if (!job?.running) return
    const id = job.id
    const timer = setInterval(async () => {
      try {
        const next = await refreshJob(id)
        if (!next.running) clearInterval(timer)
      } catch {
        clearInterval(timer)
      }
    }, 2000)
    return () => clearInterval(timer)
  }, [job?.id, job?.running, refreshJob])

  useEffect(() => {
    if (!job || selectedPage == null) return
    loadPage(job.id, selectedPage).catch(err => {
      setError(err instanceof APIError ? err.message : 'Failed to load page')
    })
  }, [job?.id, selectedPage, loadPage])

  const handleUpload = async (file: File | null) => {
    if (!file) return
    setError(null)
    setBusy(true)
    setCompareResults(null)
    setPageDetail(null)
    setSelectedPage(null)
    try {
      const created = await createOcrAssistJob(file)
      setJob(created)
    } catch (err) {
      setError(
        err instanceof APIError
          ? err.status === 404
            ? 'OCR assist API is off. Set OCR_ASSIST_LOCAL=true on the backend and restart.'
            : err.message
          : 'Upload failed'
      )
      setJob(null)
    } finally {
      setBusy(false)
    }
  }

  const runAction = async (
    action: 'accept' | 'edit_accept' | 'retry' | 'compare_vision' | 'accept_vision',
    extra?: { text?: string; provider?: 'anthropic' | 'gemini' }
  ) => {
    if (!job || selectedPage == null) return
    setBusy(true)
    setError(null)
    try {
      const result = await postOcrAssistPageAction(job.id, selectedPage, {
        action,
        ...extra,
      })
      if (result.compare?.results) {
        setCompareResults(result.compare.results)
      }
      setPageDetail(result.page)
      setEditText(result.page.final_text ?? result.page.latest_ocr_text ?? editText)
      await refreshJob(job.id)
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Layout title="OCR Assist (local)" showBackLink>
      <div className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-8">
          <PageTitle>Interactive OCR (local QA)</PageTitle>
          <p className="text-lg text-gray-600 leading-relaxed">
            Feature branch only — BDRC bulk run, then accept / edit / retry / compare
            vision per page. Requires <code className="text-sm">OCR_ASSIST_LOCAL=true</code>{' '}
            on the backend.
          </p>
        </div>

        <div className="mt-8 space-y-2">
          <label className="block text-sm font-medium text-gray-700">Upload PDF</label>
          <input
            type="file"
            accept="application/pdf,.pdf"
            disabled={busy}
            onChange={e => handleUpload(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-600"
          />
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
            {error}
          </p>
        )}

        {job && (
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
            <aside className="lg:col-span-1 space-y-4">
              <div className="text-sm text-gray-600">
                <div>
                  Job <span className="font-mono text-gray-900">{job.id}</span>
                </div>
                <div>
                  {job.running ? 'BDRC running…' : 'Idle'} · {job.page_count} pages
                </div>
              </div>
              {job.docx_ready && (
                <a
                  href={ocrAssistDocxUrl(job.id)}
                  className="inline-block text-sm font-medium text-blue-700 hover:underline"
                >
                  Download DOCX
                </a>
              )}
              <ul className="divide-y divide-gray-200 border border-gray-200 rounded bg-white">
                {job.pages.map(p => (
                  <li key={p.index}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedPage(p.index)
                        setCompareResults(null)
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                        selectedPage === p.index ? 'bg-gray-100' : ''
                      }`}
                    >
                      <span className="font-medium">Page {p.index}</span>
                      <span className="ml-2 text-gray-500">{p.status}</span>
                      {p.composite_score != null && (
                        <span className="ml-2 text-gray-400">
                          {p.composite_score.toFixed(2)}
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </aside>

            <section className="lg:col-span-2 space-y-4">
              {!pageDetail && (
                <p className="text-sm text-gray-500">Select a page to review.</p>
              )}
              {pageDetail && job && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h2 className="text-sm font-medium text-gray-700 mb-2">
                        Page {pageDetail.index} image
                      </h2>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={ocrAssistImageUrl(job.id, pageDetail.index)}
                        alt={`Page ${pageDetail.index}`}
                        className="w-full border border-gray-200 bg-white"
                      />
                    </div>
                    <div>
                      <h2 className="text-sm font-medium text-gray-700 mb-2">OCR text</h2>
                      <textarea
                        value={editText}
                        onChange={e => setEditText(e.target.value)}
                        rows={16}
                        className="w-full text-lg border border-gray-300 rounded p-3 bg-white"
                        style={{ fontFamily: 'Noto Sans Tibetan, Jomolhari, serif' }}
                      />
                      {pageDetail.latest_quality && (
                        <p className="mt-2 text-xs text-gray-500">
                          Score:{' '}
                          {String(
                            (pageDetail.latest_quality as { composite_score?: number })
                              .composite_score ?? '—'
                          )}{' '}
                          · attempts: {pageDetail.attempts.length}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => runAction('accept')}
                      className="px-3 py-2 text-sm bg-gray-900 text-white rounded disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => runAction('edit_accept', { text: editText })}
                      className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                    >
                      Save edit &amp; accept
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => runAction('retry')}
                      className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                    >
                      Retry page (BDRC)
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => runAction('compare_vision')}
                      className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                    >
                      Compare vision (Claude + Gemini)
                    </button>
                  </div>

                  {compareResults && compareResults.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                      {compareResults.map(r => (
                        <div
                          key={r.provider}
                          className="border border-gray-200 rounded p-3 bg-white space-y-2"
                        >
                          <h3 className="text-sm font-semibold capitalize">{r.provider}</h3>
                          {r.error ? (
                            <p className="text-sm text-red-600">{r.error}</p>
                          ) : (
                            <>
                              <p className="text-xs text-gray-500">
                                score:{' '}
                                {r.composite_score != null
                                  ? r.composite_score.toFixed(3)
                                  : '—'}
                              </p>
                              <pre
                                className="whitespace-pre-wrap text-sm max-h-48 overflow-auto"
                                style={{ fontFamily: 'Noto Sans Tibetan, Jomolhari, serif' }}
                              >
                                {r.transcript?.text ?? ''}
                              </pre>
                              <button
                                type="button"
                                disabled={busy || !r.transcript?.text}
                                onClick={() =>
                                  runAction('accept_vision', {
                                    provider: r.provider as 'anthropic' | 'gemini',
                                  })
                                }
                                className="px-2 py-1 text-xs bg-gray-900 text-white rounded disabled:opacity-50"
                              >
                                Use {r.provider}
                              </button>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </section>
          </div>
        )}
      </div>
    </Layout>
  )
}
