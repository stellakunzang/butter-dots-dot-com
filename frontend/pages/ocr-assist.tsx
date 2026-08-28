/**
 * Interactive OCR review UI.
 * Requires backend OCR_ASSIST_LOCAL=true. Not linked from main nav yet.
 */
import React, { useCallback, useEffect, useState } from 'react'
import { Layout, PageTitle } from '@/components'
import { ErrorDisplay } from '@/components/spellcheck'
import { APIError, SpellCheckError } from '@/lib/api'
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

type ReviewMode = 'proof' | 'ai'
/** Active tab in the Vision column (AI review mode). */
type VisionTab = 'anthropic' | 'gemini'
/** Which reading the left edit buffer currently represents. */
type LeftSource = 'bdrc' | VisionTab
type VisionModelChoice = 'both' | 'anthropic' | 'gemini'

const VISION_MODEL_OPTIONS: { value: VisionModelChoice; label: string }[] = [
  { value: 'both', label: 'Claude + Gemini' },
  { value: 'anthropic', label: 'Claude only' },
  { value: 'gemini', label: 'Gemini only' },
]

const VISION_TABS: VisionTab[] = ['anthropic', 'gemini']

function providersForChoice(
  choice: VisionModelChoice
): Array<'anthropic' | 'gemini'> {
  if (choice === 'anthropic') return ['anthropic']
  if (choice === 'gemini') return ['gemini']
  return ['anthropic', 'gemini']
}

const PROVIDER_LABELS: Record<string, string> = {
  bdrc: 'BDRC OCR',
  anthropic: 'Claude',
  gemini: 'Gemini',
}

const PAGE_STATUS_LABELS: Record<string, string> = {
  final: 'Accepted',
  needs_review: 'Needs review',
  pending: 'OCR…',
}

/** Page has finished OCR and can be opened for review. */
function pageIsSelectable(status: string): boolean {
  return status !== 'pending'
}

function firstSelectablePageIndex(
  pages: OcrAssistJob['pages']
): number | null {
  const found = pages.find(p => pageIsSelectable(p.status))
  return found ? found.index : null
}

function nextSelectablePageIndex(
  pages: OcrAssistJob['pages'],
  afterIndex: number
): number | null {
  const found = pages.find(
    p => p.index > afterIndex && pageIsSelectable(p.status)
  )
  return found ? found.index : null
}

function jobProgressLabel(job: OcrAssistJob): string {
  const ready = job.pages.filter(p => pageIsSelectable(p.status)).length
  const accepted = job.pages.filter(p => p.status === 'final').length
  const needsReview = job.pages.filter(p => p.status === 'needs_review').length
  if (job.running || ready < job.page_count) {
    return `OCR in progress · ${ready}/${job.page_count} ready`
  }
  if (accepted === job.page_count) {
    return `All ${job.page_count} pages accepted`
  }
  return `${accepted} accepted · ${needsReview} need review · ${job.page_count} pages`
}

function countIssues(errors: SpellCheckError[] | null | undefined): {
  structural: number
  unknown: number
} {
  if (!errors) return { structural: 0, unknown: 0 }
  let structural = 0
  let unknown = 0
  for (const e of errors) {
    if (e.severity === 'info') continue
    if (e.error_type === 'unknown_word') unknown += 1
    else structural += 1
  }
  return { structural, unknown }
}

function formatConfidence(quality: Record<string, unknown> | null | undefined): string | null {
  const conf = quality?.ocr_confidence
  if (typeof conf === 'number' && Number.isFinite(conf)) {
    return `${Math.round(conf * 100)}%`
  }
  return null
}

/** Degrees clockwise from page settings (same convention as BDRC OCR). */
function displayRotationDegrees(settings: Record<string, unknown> | null | undefined): number {
  const raw = settings?.rotate
  const n = typeof raw === 'number' ? raw : typeof raw === 'string' ? Number(raw) : 0
  if (!Number.isFinite(n) || Math.abs(n) < 1e-6) return 0
  return normalizeDegrees(n)
}

/** Match backend ``MIN_TIBETAN_SYLLABLES`` — near-empty often means sideways scan. */
const MIN_TIBETAN_SYLLABLES = 3

function isNearEmptyOcr(quality: Record<string, unknown> | null | undefined): boolean {
  const n = quality?.tibetan_syllable_count
  return typeof n === 'number' && Number.isFinite(n) && n < MIN_TIBETAN_SYLLABLES
}

function normalizeDegrees(n: number): number {
  let deg = ((n % 360) + 360) % 360
  if (deg > 180) deg -= 360
  return deg === 0 ? 0 : deg
}

/** True when rotation swaps width/height (90° / 270° / −90°). */
function isQuarterTurn(rotateDeg: number): boolean {
  return Math.abs(rotateDeg) % 180 === 90
}

/**
 * Layout for a page image that may be CSS-rotated.
 * The stage matches the post-rotation bounding box so the scroll viewport
 * is not sized to the unrotated (sideways) image.
 */
function rotatedImageLayout(
  naturalW: number,
  naturalH: number,
  rotateDeg: number,
  zoom: number,
  fitWidthPx: number
): { stageW: number; stageH: number; imgW: number; imgH: number } {
  const w = Math.max(1, fitWidthPx) * zoom
  if (!isQuarterTurn(rotateDeg)) {
    const h = w * (naturalH / naturalW)
    return { stageW: w, stageH: h, imgW: w, imgH: h }
  }
  // After 90°/270°, visual size is swapped relative to the unrotated img box.
  const stageW = w
  const stageH = w * (naturalW / naturalH)
  return { stageW, stageH, imgW: stageH, imgH: stageW }
}

function useElementContentWidth(): {
  ref: (node: HTMLDivElement | null) => void
  width: number
} {
  const [node, setNode] = useState<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    if (!node) {
      setWidth(0)
      return
    }
    const update = (entry?: ResizeObserverEntry) => {
      const next = entry?.contentRect.width ?? node.clientWidth
      setWidth(next > 0 ? next : 0)
    }
    update()
    const ro = new ResizeObserver(entries => update(entries[0]))
    ro.observe(node)
    return () => ro.disconnect()
  }, [node])

  return { ref: setNode, width }
}

type PageImageProps = {
  src: string
  alt: string
  rotateDeg: number
  zoom: number
  fitWidthPx: number
  onClick?: () => void
  className?: string
}

function PageImage({
  src,
  alt,
  rotateDeg,
  zoom,
  fitWidthPx,
  onClick,
  className,
}: PageImageProps) {
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null)

  useEffect(() => {
    setNatural(null)
  }, [src])

  const layout =
    natural && fitWidthPx > 0
      ? rotatedImageLayout(natural.w, natural.h, rotateDeg, zoom, fitWidthPx)
      : null

  return (
    <div
      className="relative mx-auto"
      style={
        layout
          ? { width: layout.stageW, height: layout.stageH }
          : { width: '100%', aspectRatio: '4 / 3' }
      }
    >
      {!layout && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-gray-50"
          aria-busy="true"
          aria-label="Loading page image"
        >
          <span
            className="h-6 w-6 rounded-full border-2 border-gray-300 border-t-gray-800 animate-spin"
            aria-hidden
          />
        </div>
      )}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        onClick={onClick}
        onLoad={e => {
          const img = e.currentTarget
          if (img.naturalWidth > 0 && img.naturalHeight > 0) {
            setNatural({ w: img.naturalWidth, h: img.naturalHeight })
          }
        }}
        className={className}
        style={
          layout
            ? {
                position: 'absolute',
                left: '50%',
                top: '50%',
                width: layout.imgW,
                height: layout.imgH,
                maxWidth: 'none',
                transform: `translate(-50%, -50%)${
                  rotateDeg !== 0 ? ` rotate(${rotateDeg}deg)` : ''
                }`,
                transformOrigin: 'center center',
              }
            : {
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                opacity: 0,
              }
        }
      />
    </div>
  )
}

function ReadingMeta({
  quality,
  structural,
  unknown,
  errorsPresent,
  textEdited,
  attempts,
}: {
  quality: Record<string, unknown> | null
  structural: number
  unknown: number
  errorsPresent: boolean
  textEdited: boolean
  attempts?: number
}) {
  const confidence = formatConfidence(quality)
  const syllables =
    typeof quality?.tibetan_syllable_count === 'number'
      ? quality.tibetan_syllable_count
      : null
  const issueCount = structural + unknown
  return (
    <div className={`mt-2 text-sm ${textEdited ? 'text-gray-400' : 'text-gray-600'}`}>
      <p>
        {confidence && (
          <span className={textEdited ? 'font-medium' : 'font-medium text-gray-900'}>
            OCR confidence {confidence}
          </span>
        )}
        {confidence && (issueCount > 0 || syllables != null) && !textEdited && (
          <span className="text-gray-400"> · </span>
        )}
        {!textEdited && issueCount > 0 && (
          <>
            <span className="font-medium text-gray-800">{structural} structural</span>
            {unknown > 0 && (
              <>
                {' '}
                · <span className="font-medium text-gray-800">{unknown} unknown</span>
              </>
            )}
          </>
        )}
        {!textEdited && issueCount === 0 && errorsPresent && (
          <span className="text-gray-800">
            {confidence ? ' · ' : ''}No issues flagged
          </span>
        )}
        {!textEdited && syllables != null && (
          <span className="text-gray-500"> · {syllables} syllables</span>
        )}
        {attempts != null && (
          <span className={textEdited ? '' : 'text-gray-400'}>
            {' '}
            · {attempts} attempt{attempts === 1 ? '' : 's'}
          </span>
        )}
      </p>
      {textEdited && (
        <p className="mt-1 text-xs text-gray-500">
          Score is for the OCR reading — not updated for your edits.
        </p>
      )}
    </div>
  )
}

export default function OcrAssistPage() {
  const [job, setJob] = useState<OcrAssistJob | null>(null)
  const [selectedPage, setSelectedPage] = useState<number | null>(null)
  const [pageDetail, setPageDetail] = useState<OcrAssistPageDetail | null>(null)
  const [editText, setEditText] = useState('')
  const [compareResults, setCompareResults] = useState<VisionProviderResult[] | null>(null)
  const [reviewMode, setReviewMode] = useState<ReviewMode>('proof')
  const [visionTab, setVisionTab] = useState<VisionTab>('anthropic')
  /** Provenance of ``editText`` for accept path (BDRC vs a vision provider). */
  const [leftSource, setLeftSource] = useState<LeftSource>('bdrc')
  const [visionModelChoice, setVisionModelChoice] = useState<VisionModelChoice>('both')
  const [busy, setBusy] = useState(false)
  const [busyLabel, setBusyLabel] = useState<string | null>(null)
  /** True while fetching page detail after a selection change. */
  const [pageLoading, setPageLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imageZoom, setImageZoom] = useState(1)
  const [imageLightbox, setImageLightbox] = useState(false)
  /** View-only rotation (degrees clockwise). Synced from OCR settings on page load. */
  const [viewRotateDeg, setViewRotateDeg] = useState(0)
  const [retryUseTps, setRetryUseTps] = useState(false)
  const [retryApplyViewRotate, setRetryApplyViewRotate] = useState(false)
  const [spellcheckOpen, setSpellcheckOpen] = useState(false)
  /** Text the OCR/AI confidence + highlights apply to; diverges when the user edits. */
  const [scoreBaselineText, setScoreBaselineText] = useState('')
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [docxConfirmOpen, setDocxConfirmOpen] = useState(false)

  const setEditFromSource = useCallback((text: string) => {
    setEditText(text)
    setScoreBaselineText(text)
  }, [])

  const refreshJob = useCallback(async (jobId: string) => {
    const next = await getOcrAssistJob(jobId)
    setJob(next)
    return next
  }, [])

  const applyCompareFromDetail = useCallback((detail: OcrAssistPageDetail) => {
    if (detail.vision_by_provider && Object.keys(detail.vision_by_provider).length > 0) {
      setCompareResults(
        Object.entries(detail.vision_by_provider).map(([provider, entry]) => ({
          provider,
          transcript: entry.transcript,
          quality: entry.quality,
          spellcheck_errors: entry.spellcheck_errors ?? null,
          composite_score:
            typeof entry.quality?.composite_score === 'number'
              ? (entry.quality.composite_score as number)
              : null,
          decision: null,
          error: null,
        }))
      )
      return true
    }
    setCompareResults(null)
    return false
  }, [])

  const loadPage = useCallback(
    async (jobId: string, pageIndex: number) => {
      const detail = await getOcrAssistPage(jobId, pageIndex)
      setPageDetail(detail)
      const text = detail.final_text ?? detail.latest_ocr_text ?? ''
      setEditFromSource(text)
      applyCompareFromDetail(detail)
      setReviewMode('proof')
      setVisionTab('anthropic')
      setLeftSource('bdrc')
      setImageZoom(1)
      setImageLightbox(false)
      setViewRotateDeg(displayRotationDegrees(detail.settings))
      setRetryUseTps(false)
      setRetryApplyViewRotate(false)
      setSuccessMessage(null)
      const { structural, unknown } = countIssues(detail.latest_spellcheck_errors)
      setSpellcheckOpen(structural + unknown > 0)
    },
    [applyCompareFromDetail, setEditFromSource]
  )

  const jobId = job?.id
  const shouldPollJob =
    Boolean(job) &&
    (Boolean(job?.running) || Boolean(job?.pages.some(p => p.status === 'pending')))

  useEffect(() => {
    if (!jobId || !shouldPollJob) return
    // Keep polling while the backend reports running, or while any page is
    // still pending (covers a race where create returned before running flipped).
    const timer = setInterval(async () => {
      try {
        const next = await refreshJob(jobId)
        const done =
          !next.running && next.pages.every(p => p.status !== 'pending')
        if (done) clearInterval(timer)
      } catch {
        clearInterval(timer)
      }
    }, 2000)
    return () => clearInterval(timer)
  }, [jobId, shouldPollJob, refreshJob])

  useEffect(() => {
    if (!docxConfirmOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDocxConfirmOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [docxConfirmOpen])

  // Open the first finished page automatically once OCR has something to show.
  useEffect(() => {
    if (!job || selectedPage != null) return
    const first = firstSelectablePageIndex(job.pages)
    if (first != null) setSelectedPage(first)
  }, [job, selectedPage])

  // If the selected page goes back to pending (e.g. mid-retry race), clear it.
  useEffect(() => {
    if (!job || selectedPage == null) return
    const summary = job.pages.find(p => p.index === selectedPage)
    if (summary && !pageIsSelectable(summary.status)) {
      setSelectedPage(null)
      setPageDetail(null)
    }
  }, [job, selectedPage])

  useEffect(() => {
    if (!job || selectedPage == null) return
    const summary = job.pages.find(p => p.index === selectedPage)
    if (!summary || !pageIsSelectable(summary.status)) return

    const jobIdForLoad = job.id
    const pageForLoad = selectedPage
    let cancelled = false
    setPageLoading(true)
    // Drop stale detail immediately so we never show page N content as page N+1.
    setPageDetail(prev => (prev?.index === pageForLoad ? prev : null))
    setError(null)

    loadPage(jobIdForLoad, pageForLoad)
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof APIError ? err.message : 'Failed to load page')
          setPageDetail(null)
        }
      })
      .finally(() => {
        if (!cancelled) setPageLoading(false)
      })

    return () => {
      cancelled = true
    }
    // Intentionally omit `job`: poll refreshes must not reload the open page.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- job.pages only used for gate
  }, [job?.id, selectedPage, loadPage])

  const handleUpload = async (file: File | null) => {
    if (!file) return
    setError(null)
    setBusy(true)
    setBusyLabel('Uploading document…')
    setCompareResults(null)
    setPageDetail(null)
    setSelectedPage(null)
    setPageLoading(false)
    setReviewMode('proof')
    setSuccessMessage(null)
    try {
      const created = await createOcrAssistJob(file)
      setJob(created)
    } catch (err) {
      setError(
        err instanceof APIError
          ? err.status === 404
            ? 'Interactive OCR is not enabled on this server.'
            : err.message
          : 'Upload failed'
      )
      setJob(null)
    } finally {
      setBusy(false)
      setBusyLabel(null)
    }
  }

  const useVisionReading = () => {
    if (!pageDetail) return
    const match = compareResults?.find(r => r.provider === visionTab)
    if (!match || match.error || !match.transcript?.text) return
    setEditFromSource(match.transcript.text)
    setLeftSource(visionTab)
    const { structural, unknown } = countIssues(match.spellcheck_errors)
    setSpellcheckOpen(structural + unknown > 0)
  }

  const backToProof = () => {
    // Keep the left edit buffer; only leave the two-column compare view.
    setReviewMode('proof')
    const { structural, unknown } = countIssues(
      leftSource === 'bdrc'
        ? pageDetail?.latest_spellcheck_errors
        : compareResults?.find(r => r.provider === leftSource)?.spellcheck_errors
    )
    setSpellcheckOpen(structural + unknown > 0)
  }

  const runAction = async (
    action: 'accept' | 'edit_accept' | 'retry' | 'compare_vision' | 'accept_vision',
    extra?: {
      text?: string
      provider?: 'anthropic' | 'gemini'
      providers?: Array<'anthropic' | 'gemini'>
      use_tps?: boolean
      rotate?: number
    },
    label?: string
  ) => {
    if (!job || selectedPage == null) return
    setBusy(true)
    setBusyLabel(label ?? 'Working…')
    setError(null)
    setSuccessMessage(null)
    try {
      const result = await postOcrAssistPageAction(job.id, selectedPage, {
        action,
        ...extra,
      })
      if (result.compare?.results) {
        setCompareResults(prev => {
          const byProvider = new Map((prev ?? []).map(r => [r.provider, r]))
          for (const r of result.compare!.results) {
            byProvider.set(r.provider, r)
          }
          // Stable order: Claude, then Gemini, then any others.
          const order = ['anthropic', 'gemini']
          const merged = Array.from(byProvider.values()).sort((a, b) => {
            const ia = order.indexOf(a.provider)
            const ib = order.indexOf(b.provider)
            return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
          })
          return merged
        })
        setReviewMode('ai')
        const firstOk =
          (result.compare.results.find(r => !r.error && r.transcript?.text)
            ?.provider as VisionTab | undefined) ??
          (result.compare.results[0]?.provider as VisionTab | undefined) ??
          'anthropic'
        setVisionTab(firstOk === 'gemini' ? 'gemini' : 'anthropic')
        // Keep BDRC (or prior edits) in the left column — do not overwrite with vision.
        if (pageDetail) {
          const { structural, unknown } = countIssues(
            pageDetail.latest_spellcheck_errors
          )
          setSpellcheckOpen(structural + unknown > 0)
        }
        setPageDetail(result.page)
        setViewRotateDeg(displayRotationDegrees(result.page.settings))
      } else {
        setPageDetail(result.page)
        setViewRotateDeg(displayRotationDegrees(result.page.settings))
        const text =
          result.page.final_text ?? result.page.latest_ocr_text ?? editText
        setEditFromSource(text)
        const { structural, unknown } = countIssues(result.page.latest_spellcheck_errors)
        setSpellcheckOpen(structural + unknown > 0)
        if (action === 'accept_vision' || action === 'accept' || action === 'edit_accept') {
          setReviewMode('proof')
          setLeftSource('bdrc')
          if (action === 'edit_accept') {
            setSuccessMessage(`Page ${selectedPage} saved with your edits.`)
          } else if (action === 'accept_vision') {
            const label = extra?.provider
              ? PROVIDER_LABELS[extra.provider] ?? extra.provider
              : 'AI'
            setSuccessMessage(`Page ${selectedPage} accepted from ${label}.`)
          } else {
            setSuccessMessage(`Page ${selectedPage} accepted.`)
          }
        } else if (action === 'retry') {
          const bits: string[] = []
          if (extra?.use_tps) bits.push('dewarp')
          if (extra?.rotate != null) bits.push(`${extra.rotate}° orientation`)
          setSuccessMessage(
            bits.length
              ? `Page ${selectedPage} retried with ${bits.join(' + ')}.`
              : `Page ${selectedPage} retried.`
          )
          setRetryUseTps(false)
          setRetryApplyViewRotate(false)
        }
        applyCompareFromDetail(result.page)
      }
      await refreshJob(job.id)
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Action failed')
    } finally {
      setBusy(false)
      setBusyLabel(null)
    }
  }

  const openReviewWithAi = async () => {
    if (!job || selectedPage == null || !pageDetail) return
    const providers = providersForChoice(visionModelChoice)
    const label =
      visionModelChoice === 'both'
        ? 'Reviewing with Claude + Gemini…'
        : visionModelChoice === 'gemini'
          ? 'Reviewing with Gemini…'
          : 'Reviewing with Claude…'
    // Always re-run the selected model(s); prior results for other models are kept.
    await runAction('compare_vision', { providers }, label)
  }

  const bdrcHighlight = {
    text: pageDetail?.latest_ocr_text ?? '',
    errors: pageDetail?.latest_spellcheck_errors ?? null,
    quality: pageDetail?.latest_quality ?? null,
  }

  const visionResult = compareResults?.find(r => r.provider === visionTab) ?? null
  const visionHighlight = {
    text: visionResult?.transcript?.text ?? '',
    errors: visionResult?.spellcheck_errors ?? null,
    quality: visionResult?.quality ?? null,
  }

  const leftSourceResult =
    leftSource === 'bdrc'
      ? null
      : compareResults?.find(r => r.provider === leftSource) ?? null
  const leftHighlight =
    leftSource === 'bdrc'
      ? bdrcHighlight
      : {
          text: leftSourceResult?.transcript?.text ?? '',
          errors: leftSourceResult?.spellcheck_errors ?? null,
          quality: leftSourceResult?.quality ?? null,
        }

  /** Proof-mode spellcheck panel (always BDRC). */
  const highlight = bdrcHighlight
  const { structural: issueStructural, unknown: issueUnknown } = countIssues(
    reviewMode === 'proof' ? highlight.errors : leftHighlight.errors
  )
  const issueCount = issueStructural + issueUnknown
  const spellcheckClean =
    (reviewMode === 'proof' ? highlight.errors : leftHighlight.errors) != null &&
    issueCount === 0
  const textEdited = editText !== scoreBaselineText

  const visionIssueCounts = countIssues(visionHighlight.errors)
  const visionIssueCount = visionIssueCounts.structural + visionIssueCounts.unknown
  const visionSpellcheckClean =
    visionHighlight.errors != null && visionIssueCount === 0
  const visionReady = Boolean(
    visionResult && !visionResult.error && visionResult.transcript?.text?.trim()
  )

  const acceptLeftColumn = () => {
    if (leftSource === 'bdrc') {
      const bdrcText = pageDetail?.final_text ?? pageDetail?.latest_ocr_text ?? ''
      if (editText === bdrcText) {
        void runAction('accept', undefined, 'Saving…')
      } else {
        void runAction('edit_accept', { text: editText }, 'Saving…')
      }
      return
    }
    void runAction(
      'accept_vision',
      { provider: leftSource, text: editText },
      'Saving…'
    )
  }
  const showBusyOverlay = busy && Boolean(busyLabel)
  const detailMatchesSelection =
    pageDetail != null &&
    selectedPage != null &&
    pageDetail.index === selectedPage
  const showPageLoading =
    pageLoading && (!detailMatchesSelection || !pageDetail)
  const ocrRotateDeg = displayRotationDegrees(pageDetail?.settings)
  const viewDiffersFromOcr = viewRotateDeg !== ocrRotateDeg
  const nearEmptyOcr = isNearEmptyOcr(
    pageDetail?.latest_quality ?? pageDetail?.final_quality
  )
  const nextPageIndex =
    job && selectedPage != null
      ? nextSelectablePageIndex(job.pages, selectedPage)
      : null
  const acceptedCount = job?.pages.filter(p => p.status === 'final').length ?? 0
  const allPagesAccepted = Boolean(
    job && acceptedCount === job.page_count && job.page_count > 0
  )
  const showDocxDownload = Boolean(job?.docx_ready)

  const startDocxDownload = () => {
    if (!job) return
    window.location.href = ocrAssistDocxUrl(job.id)
  }

  const handleDocxClick = () => {
    if (!job) return
    if (allPagesAccepted) {
      startDocxDownload()
      return
    }
    setDocxConfirmOpen(true)
  }

  const nudgeViewRotate = (delta: number) => {
    setViewRotateDeg(d => {
      const next = normalizeDegrees(d + delta)
      setRetryApplyViewRotate(next !== ocrRotateDeg)
      return next
    })
  }

  const resetViewToOcr = () => {
    setViewRotateDeg(ocrRotateDeg)
    setRetryApplyViewRotate(false)
  }

  const { ref: imageViewportRef, width: imageViewportWidth } =
    useElementContentWidth()
  const { ref: lightboxViewportRef, width: lightboxViewportWidth } =
    useElementContentWidth()
  const pageImageSrc =
    job && pageDetail ? ocrAssistImageUrl(job.id, pageDetail.index) : ''

  return (
    <Layout title="Interactive OCR" showBackLink>
      <div className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-8">
          <PageTitle>Interactive OCR</PageTitle>
          <p className="text-lg text-gray-600 leading-relaxed max-w-3xl">
            Review each page against the source image. Pages unlock after OCR
            finishes; accept or edit each one. Download DOCX includes accepted
            pages only — you can export before the whole document is done.
          </p>
        </div>

        <div className="mt-8 space-y-2">
          <label className="block text-sm font-medium text-gray-700">Upload PDF</label>
          <input
            type="file"
            accept="application/pdf,.pdf"
            disabled={busy}
            onChange={e => handleUpload(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-600 disabled:opacity-50"
          />
          {busy && busyLabel && (
            <div
              className="flex items-center gap-2 text-sm text-gray-700"
              aria-live="polite"
              aria-busy="true"
            >
              <span
                className="h-4 w-4 shrink-0 rounded-full border-2 border-gray-300 border-t-gray-800 animate-spin"
                aria-hidden
              />
              <span>{busyLabel}</span>
            </div>
          )}
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
                <div aria-live="polite">{jobProgressLabel(job)}</div>
                {!job.docx_ready && acceptedCount === 0 && (
                  <div className="mt-1 text-xs text-gray-500">
                    Download DOCX appears after the first page is accepted.
                  </div>
                )}
                {showDocxDownload && !allPagesAccepted && (
                  <div className="mt-1 text-xs text-gray-500">
                    Partial export available ({acceptedCount}/{job.page_count}{' '}
                    accepted). Unaccepted pages are omitted.
                  </div>
                )}
              </div>
              {showDocxDownload && (
                <button
                  type="button"
                  onClick={handleDocxClick}
                  className="inline-block text-sm font-medium text-blue-700 hover:underline"
                >
                  Download DOCX
                </button>
              )}
              <ul className="divide-y divide-gray-200 border border-gray-200 rounded bg-white">
                {job.pages.map(p => {
                  const selectable = pageIsSelectable(p.status)
                  const disabled = busy || !selectable
                  return (
                    <li key={p.index}>
                      <button
                        type="button"
                        disabled={disabled}
                        title={
                          !selectable
                            ? 'Available after OCR finishes this page'
                            : undefined
                        }
                        onClick={() => {
                          setSelectedPage(p.index)
                          setCompareResults(null)
                          setReviewMode('proof')
                        }}
                        className={`w-full text-left px-3 py-2 text-sm disabled:cursor-not-allowed ${
                          selectable ? 'hover:bg-gray-50' : 'opacity-50'
                        } ${selectedPage === p.index ? 'bg-gray-100' : ''} ${
                          busy ? 'disabled:opacity-50' : ''
                        }`}
                      >
                        <span className="font-medium">Page {p.index}</span>
                        <span className="ml-2 text-gray-500">
                          {PAGE_STATUS_LABELS[p.status] ?? p.status}
                        </span>
                        {p.status === 'pending' && (
                          <span
                            className="ml-2 inline-block h-3 w-3 align-middle rounded-full border-2 border-gray-300 border-t-gray-700 animate-spin"
                            aria-hidden
                          />
                        )}
                        {p.ocr_confidence != null && selectable && (
                          <span className="ml-2 text-gray-400">
                            {Math.round(p.ocr_confidence * 100)}%
                          </span>
                        )}
                        {p.ocr_confidence == null &&
                          p.composite_score != null &&
                          selectable && (
                            <span className="ml-2 text-gray-400">
                              {p.composite_score.toFixed(2)}
                            </span>
                          )}
                        {busy && selectedPage === p.index && (
                          <span className="ml-2 text-blue-600">Working…</span>
                        )}
                      </button>
                    </li>
                  )
                })}
              </ul>
            </aside>

            <section className="lg:col-span-2 relative min-h-[24rem]">
              {(showBusyOverlay || showPageLoading) && (
                <div
                  className="absolute inset-0 z-10 flex items-center justify-center rounded bg-white/80 backdrop-blur-[1px]"
                  aria-live="polite"
                  aria-busy="true"
                >
                  <div className="flex flex-col items-center gap-3 px-6 py-4">
                    <span
                      className="h-8 w-8 rounded-full border-2 border-gray-300 border-t-gray-800 animate-spin"
                      aria-hidden
                    />
                    <p className="text-sm font-medium text-gray-800">
                      {showBusyOverlay
                        ? busyLabel
                        : selectedPage != null
                          ? `Loading page ${selectedPage}…`
                          : 'Loading…'}
                    </p>
                  </div>
                </div>
              )}

              {!detailMatchesSelection && !showPageLoading && (
                <p className="text-sm text-gray-500">
                  {job.running || job.pages.some(p => p.status === 'pending')
                    ? 'OCR is running. Pages unlock here as each one finishes — you can review ready pages while others process.'
                    : 'Select a page to review.'}
                </p>
              )}

              {detailMatchesSelection && job && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="text-sm font-medium text-gray-800">
                      Page {pageDetail.index}
                      {pageDetail.status === 'final' && (
                        <span className="ml-2 inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800">
                          Accepted
                        </span>
                      )}
                      {pageDetail.status === 'needs_review' && (
                        <span className="ml-2 inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-900">
                          Needs review
                        </span>
                      )}
                      {reviewMode === 'ai' && (
                        <span className="ml-2 font-normal text-gray-500">
                          · Review with AI
                        </span>
                      )}
                    </h2>
                    {reviewMode === 'ai' && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => backToProof()}
                        className="text-sm text-gray-600 hover:text-gray-900 underline disabled:opacity-50"
                      >
                        Back to proof
                      </button>
                    )}
                  </div>

                  {successMessage && (
                    <div
                      className="flex flex-wrap items-center gap-3 text-sm text-green-900 bg-green-50 border border-green-200 rounded px-3 py-2"
                      role="status"
                      aria-live="polite"
                    >
                      <svg
                        className="w-5 h-5 text-green-600 shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <span className="font-medium flex-1">{successMessage}</span>
                      {nextPageIndex != null && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => {
                              setSuccessMessage(null)
                              setSelectedPage(nextPageIndex)
                              setCompareResults(null)
                              setReviewMode('proof')
                            }}
                            className="px-2.5 py-1 text-sm font-medium bg-green-700 text-white rounded hover:bg-green-800 disabled:opacity-50"
                          >
                            Next page
                          </button>
                        )}
                      <button
                        type="button"
                        onClick={() => setSuccessMessage(null)}
                        className="text-green-800/70 hover:text-green-900 text-xs underline"
                      >
                        Dismiss
                      </button>
                    </div>
                  )}

                  {nearEmptyOcr &&
                    pageDetail.status === 'needs_review' &&
                    reviewMode === 'proof' && (
                      <div
                        className="text-sm text-amber-950 bg-amber-50 border border-amber-200 rounded px-3 py-2 space-y-1"
                        role="status"
                      >
                        <p className="font-medium">
                          Almost no Tibetan was read — this page may be sideways
                        </p>
                        <p className="text-amber-900/90">
                          Use ↺ / ↻ above the image to turn it for viewing (display
                          only). Then check &ldquo;Re-OCR at view orientation&rdquo;
                          and Retry page so BDRC uses that angle.
                          {viewDiffersFromOcr && !retryApplyViewRotate
                            ? ' Your view is turned — enable the checkbox to apply it.'
                            : viewDiffersFromOcr && retryApplyViewRotate
                              ? ` Ready to re-OCR at ${viewRotateDeg}°.`
                              : ''}
                        </p>
                      </div>
                    )}

                  {reviewMode === 'ai' && (
                    <p className="text-sm text-gray-600">
                      Separate full-page reading — switch tabs to A/B Claude vs Gemini.
                      Does not merge with BDRC. Use a vision reading only after checking
                      it against the scan.
                    </p>
                  )}

                  {reviewMode === 'ai' && visionResult?.error && (
                    <div className="text-sm text-red-800 bg-red-50 border border-red-200 rounded px-3 py-2 space-y-1">
                      <p className="font-medium">
                        {PROVIDER_LABELS[visionTab]} could not produce a reading
                      </p>
                      <p className="font-mono text-xs whitespace-pre-wrap break-words">
                        {visionResult.error}
                      </p>
                    </div>
                  )}

                  {/* Stacked proofing: image → spellcheck → edit → confidence → actions */}
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <h3 className="text-sm font-medium text-gray-700">
                          Page image
                          {viewRotateDeg !== 0 && (
                            <span className="ml-2 font-normal text-gray-500">
                              · view {viewRotateDeg}&deg;
                              {viewDiffersFromOcr
                                ? ' (display only — not used by OCR yet)'
                                : ocrRotateDeg !== 0
                                  ? ' (matches OCR orientation)'
                                  : ''}
                            </span>
                          )}
                          {viewRotateDeg === 0 && ocrRotateDeg !== 0 && (
                            <span className="ml-2 font-normal text-gray-500">
                              · OCR orientation {ocrRotateDeg}&deg;
                            </span>
                          )}
                        </h3>
                        <div className="flex flex-wrap items-center gap-1">
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => nudgeViewRotate(-90)}
                            className="px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                            title="Turn image 90° counter-clockwise (view only)"
                            aria-label="Turn view counter-clockwise"
                          >
                            ↺ 90°
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => nudgeViewRotate(90)}
                            className="px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                            title="Turn image 90° clockwise (view only)"
                            aria-label="Turn view clockwise"
                          >
                            ↻ 90°
                          </button>
                          {viewDiffersFromOcr && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={resetViewToOcr}
                              className="px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                              title="Reset view to current OCR orientation"
                            >
                              Reset view
                            </button>
                          )}
                          <span className="mx-1 text-gray-300" aria-hidden>
                            |
                          </span>
                          <button
                            type="button"
                            disabled={busy || imageZoom <= 1}
                            onClick={() =>
                              setImageZoom(z => Math.max(1, Number((z - 0.25).toFixed(2))))
                            }
                            className="px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                            aria-label="Zoom out"
                          >
                            −
                          </button>
                          <span className="text-xs text-gray-500 w-10 text-center tabular-nums">
                            {Math.round(imageZoom * 100)}%
                          </span>
                          <button
                            type="button"
                            disabled={busy || imageZoom >= 3}
                            onClick={() =>
                              setImageZoom(z => Math.min(3, Number((z + 0.25).toFixed(2))))
                            }
                            className="px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                            aria-label="Zoom in"
                          >
                            +
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => setImageLightbox(true)}
                            className="ml-1 px-2 py-0.5 text-sm border border-gray-300 rounded disabled:opacity-40"
                          >
                            Enlarge
                          </button>
                        </div>
                      </div>
                      <div
                        ref={imageViewportRef}
                        className="overflow-auto border border-gray-200 bg-white max-h-[50vh] p-2"
                      >
                        <PageImage
                          src={pageImageSrc}
                          alt={`Page ${pageDetail.index}`}
                          rotateDeg={viewRotateDeg}
                          zoom={imageZoom}
                          fitWidthPx={imageViewportWidth}
                          onClick={() => !busy && setImageLightbox(true)}
                          className="block cursor-zoom-in bg-white"
                        />
                      </div>
                    </div>

                    {reviewMode === 'proof' && highlight.errors != null && (
                      <div className="border border-gray-200 rounded overflow-hidden bg-white">
                        <button
                          type="button"
                          onClick={() => setSpellcheckOpen(o => !o)}
                          className={`w-full flex items-center gap-2 px-3 py-2.5 text-left text-sm ${
                            spellcheckClean
                              ? 'bg-green-50 text-green-900 hover:bg-green-100'
                              : 'bg-gray-50 text-gray-800 hover:bg-gray-100'
                          }`}
                          aria-expanded={spellcheckOpen}
                        >
                          {spellcheckClean ? (
                            <>
                              <svg
                                className="w-5 h-5 text-green-600 shrink-0"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                aria-hidden
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                              <span className="font-medium">No spelling issues</span>
                            </>
                          ) : (
                            <span className="font-medium">
                              Spellcheck · {issueStructural} structural
                              {issueUnknown > 0 ? ` · ${issueUnknown} unknown` : ''}
                            </span>
                          )}
                          <span className="ml-auto text-xs opacity-70">
                            {spellcheckOpen ? 'Hide' : 'Show'}
                          </span>
                        </button>
                        {spellcheckOpen && highlight.text && highlight.errors && (
                          <div className="p-3 border-t border-gray-200 max-h-[40vh] overflow-auto resize-y min-h-[8rem]">
                            <ErrorDisplay
                              response={{
                                text: highlight.text,
                                error_count: highlight.errors.length,
                                errors: highlight.errors,
                              }}
                            />
                            {!spellcheckClean && (
                              <p className="mt-2 text-xs text-gray-500">
                                Red = structural · yellow = unknown syllable. Edit below
                                before accepting.
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {reviewMode === 'proof' ? (
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">
                          Edit text
                        </h3>
                        <textarea
                          value={editText}
                          onChange={e => setEditText(e.target.value)}
                          rows={12}
                          disabled={busy}
                          className="w-full min-h-[12rem] text-lg border border-gray-300 rounded p-3 bg-white disabled:opacity-60 resize-y"
                          style={{
                            fontFamily: 'Noto Sans Tibetan, Jomolhari, serif',
                          }}
                        />
                        <ReadingMeta
                          quality={highlight.quality}
                          structural={issueStructural}
                          unknown={issueUnknown}
                          errorsPresent={highlight.errors != null}
                          textEdited={textEdited}
                          attempts={pageDetail.attempts.length}
                        />
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
                        <div className="min-w-0 space-y-3 border border-gray-200 rounded-lg p-3 bg-white">
                          <div>
                            <h3 className="text-sm font-medium text-gray-800">
                              BDRC OCR
                              {leftSource !== 'bdrc' && (
                                <span className="ml-2 font-normal text-amber-800">
                                  · edit buffer from {PROVIDER_LABELS[leftSource]}
                                </span>
                              )}
                            </h3>
                            <p className="text-xs text-gray-500 mt-0.5">
                              Editable. Accept from this column, or copy a vision
                              reading into it first.
                            </p>
                          </div>
                          {leftHighlight.errors != null && leftHighlight.text && (
                            <div className="border border-gray-200 rounded overflow-hidden">
                              <div
                                className={`px-2.5 py-1.5 text-xs font-medium ${
                                  spellcheckClean
                                    ? 'bg-green-50 text-green-900'
                                    : 'bg-gray-50 text-gray-800'
                                }`}
                              >
                                {spellcheckClean
                                  ? 'No spelling issues'
                                  : `Spellcheck · ${issueStructural} structural${
                                      issueUnknown > 0
                                        ? ` · ${issueUnknown} unknown`
                                        : ''
                                    }`}
                              </div>
                              <div className="p-2 max-h-[20vh] overflow-auto border-t border-gray-200">
                                <ErrorDisplay
                                  response={{
                                    text: leftHighlight.text,
                                    error_count: leftHighlight.errors.length,
                                    errors: leftHighlight.errors,
                                  }}
                                />
                              </div>
                            </div>
                          )}
                          <textarea
                            value={editText}
                            onChange={e => setEditText(e.target.value)}
                            rows={14}
                            disabled={busy}
                            className="w-full min-h-[14rem] text-base border border-gray-300 rounded p-2.5 bg-white disabled:opacity-60 resize-y"
                            style={{
                              fontFamily: 'Noto Sans Tibetan, Jomolhari, serif',
                            }}
                          />
                          <ReadingMeta
                            quality={leftHighlight.quality}
                            structural={issueStructural}
                            unknown={issueUnknown}
                            errorsPresent={leftHighlight.errors != null}
                            textEdited={textEdited}
                            attempts={pageDetail.attempts.length}
                          />
                        </div>

                        <div className="min-w-0 space-y-3 border border-gray-200 rounded-lg p-3 bg-gray-50/60">
                          <div>
                            <h3 className="text-sm font-medium text-gray-800">
                              Vision OCR
                            </h3>
                            <p className="text-xs text-gray-500 mt-0.5">
                              Read-only alternate reading. Switch tabs to compare
                              models.
                            </p>
                          </div>
                          <div className="flex flex-wrap gap-1.5" role="tablist">
                            {VISION_TABS.map(id => {
                              const result = compareResults?.find(r => r.provider === id)
                              const missing = !result
                              const failed = Boolean(result?.error)
                              return (
                                <button
                                  key={id}
                                  type="button"
                                  role="tab"
                                  aria-selected={visionTab === id}
                                  disabled={busy || missing}
                                  onClick={() => setVisionTab(id)}
                                  title={
                                    failed
                                      ? result?.error ?? 'Provider failed'
                                      : missing
                                        ? 'No result yet — run Review with AI'
                                        : undefined
                                  }
                                  className={`px-2.5 py-1 text-sm rounded border disabled:opacity-40 ${
                                    visionTab === id
                                      ? failed
                                        ? 'bg-red-800 text-white border-red-800'
                                        : 'bg-gray-900 text-white border-gray-900'
                                      : failed
                                        ? 'bg-red-50 text-red-800 border-red-300'
                                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                  }`}
                                >
                                  {PROVIDER_LABELS[id]}
                                  {failed && (
                                    <span className="ml-1 opacity-90">failed</span>
                                  )}
                                  {!failed &&
                                    typeof result?.quality?.ocr_confidence ===
                                      'number' && (
                                      <span className="ml-1 opacity-80">
                                        {Math.round(
                                          (result.quality.ocr_confidence as number) *
                                            100
                                        )}
                                        %
                                      </span>
                                    )}
                                  {!failed &&
                                    typeof result?.quality?.ocr_confidence !==
                                      'number' &&
                                    result?.composite_score != null && (
                                      <span className="ml-1 opacity-80">
                                        {result.composite_score.toFixed(2)}
                                      </span>
                                    )}
                                </button>
                              )
                            })}
                          </div>
                          {visionResult?.error ? (
                            <p className="text-sm text-red-800">
                              {PROVIDER_LABELS[visionTab]} failed — try Run again or
                              another model.
                            </p>
                          ) : !visionReady ? (
                            <p className="text-sm text-gray-500">
                              No reading for {PROVIDER_LABELS[visionTab]} yet.
                            </p>
                          ) : (
                            <>
                              {visionHighlight.errors != null && (
                                <div className="border border-gray-200 rounded overflow-hidden bg-white">
                                  <div
                                    className={`px-2.5 py-1.5 text-xs font-medium ${
                                      visionSpellcheckClean
                                        ? 'bg-green-50 text-green-900'
                                        : 'bg-gray-50 text-gray-800'
                                    }`}
                                  >
                                    {visionSpellcheckClean
                                      ? 'No spelling issues'
                                      : `Spellcheck · ${visionIssueCounts.structural} structural${
                                          visionIssueCounts.unknown > 0
                                            ? ` · ${visionIssueCounts.unknown} unknown`
                                            : ''
                                        }`}
                                  </div>
                                  <div className="p-2 max-h-[20vh] overflow-auto border-t border-gray-200">
                                    <ErrorDisplay
                                      response={{
                                        text: visionHighlight.text,
                                        error_count: visionHighlight.errors.length,
                                        errors: visionHighlight.errors,
                                      }}
                                    />
                                  </div>
                                </div>
                              )}
                              <div
                                className="w-full min-h-[14rem] max-h-[28rem] overflow-auto text-base border border-gray-200 rounded p-2.5 bg-white whitespace-pre-wrap"
                                style={{
                                  fontFamily: 'Noto Sans Tibetan, Jomolhari, serif',
                                }}
                              >
                                {visionHighlight.text}
                              </div>
                              <ReadingMeta
                                quality={visionHighlight.quality}
                                structural={visionIssueCounts.structural}
                                unknown={visionIssueCounts.unknown}
                                errorsPresent={visionHighlight.errors != null}
                                textEdited={false}
                              />
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {reviewMode === 'proof' && (
                    <div className="flex flex-col gap-2 px-3 py-2.5 border border-gray-200 rounded bg-slate-50/90">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          Optional: Vision OCR
                        </p>
                        <p className="mt-1 text-xs text-gray-600 leading-relaxed max-w-3xl">
                          When BDRC is close but you want another reading of the
                          image, run Claude and/or Gemini. This calls paid APIs
                          (Opus / Gemini Pro) — prefer a single model for
                          iteration, both only when comparing.
                        </p>
                        <p className="mt-1.5 text-xs text-gray-600 leading-relaxed max-w-3xl">
                          Vision returns a separate full-page reading, not a
                          patch of flagged syllables and not a merge with BDRC.
                          It may look spellcheck-clean but still diverge from the
                          image. Compare it against the scan and choose one
                          reading — don&apos;t treat vision as ground truth.
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => openReviewWithAi()}
                          className="px-3 py-2 text-sm border border-gray-300 rounded bg-white disabled:opacity-50"
                        >
                          Review with AI
                        </button>
                        <label className="flex items-center gap-1.5 text-sm text-gray-600">
                          <span className="sr-only">Vision model</span>
                          <select
                            value={visionModelChoice}
                            disabled={busy}
                            onChange={e =>
                              setVisionModelChoice(
                                e.target.value as VisionModelChoice
                              )
                            }
                            className="text-sm border border-gray-300 rounded px-2 py-1.5 bg-white disabled:opacity-50"
                          >
                            {VISION_MODEL_OPTIONS.map(opt => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </div>
                  )}

                  <div className="sticky bottom-0 z-[5] -mx-1 px-1 py-3 bg-gradient-to-t from-white via-white to-transparent border-t border-gray-100">
                    <div className="flex flex-wrap gap-2 items-stretch">
                      {reviewMode === 'proof' ? (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => runAction('accept', undefined, 'Saving…')}
                            className="px-3 py-2 text-sm bg-gray-900 text-white rounded disabled:opacity-50"
                          >
                            Accept
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() =>
                              runAction(
                                'edit_accept',
                                { text: editText },
                                'Saving…'
                              )
                            }
                            className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                          >
                            Save edit &amp; accept
                          </button>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-2 py-1.5 border border-gray-200 rounded bg-gray-50/80">
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => {
                                const flags: {
                                  use_tps?: boolean
                                  rotate?: number
                                } = {}
                                if (retryUseTps) flags.use_tps = true
                                if (retryApplyViewRotate) flags.rotate = viewRotateDeg
                                const label =
                                  retryUseTps && retryApplyViewRotate
                                    ? 'Retrying with dewarp + orientation…'
                                    : retryUseTps
                                      ? 'Retrying with dewarp…'
                                      : retryApplyViewRotate
                                        ? 'Retrying with view orientation…'
                                        : 'Retrying OCR…'
                                void runAction('retry', flags, label)
                              }}
                              className="px-3 py-2 text-sm border border-gray-300 rounded bg-white disabled:opacity-50"
                            >
                              Retry page
                            </button>
                            <label className="flex items-center gap-1.5 text-sm text-gray-700">
                              <input
                                type="checkbox"
                                checked={retryUseTps}
                                disabled={busy}
                                onChange={e => setRetryUseTps(e.target.checked)}
                                className="rounded border-gray-300"
                              />
                              Dewarp curved page (TPS)
                            </label>
                            <label
                              className="flex items-center gap-1.5 text-sm text-gray-700"
                              title={
                                viewDiffersFromOcr
                                  ? `Send view angle (${viewRotateDeg}°) into OCR settings on retry`
                                  : 'Turn the page image first, then enable this to re-OCR at that angle'
                              }
                            >
                              <input
                                type="checkbox"
                                checked={retryApplyViewRotate}
                                disabled={busy}
                                onChange={e =>
                                  setRetryApplyViewRotate(e.target.checked)
                                }
                                className="rounded border-gray-300"
                              />
                              Re-OCR at view orientation
                              {retryApplyViewRotate ? ` (${viewRotateDeg}°)` : ''}
                            </label>
                          </div>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            disabled={busy || !editText.trim()}
                            onClick={() => acceptLeftColumn()}
                            className="px-3 py-2 text-sm bg-gray-900 text-white rounded disabled:opacity-50"
                          >
                            {leftSource === 'bdrc'
                              ? textEdited
                                ? 'Save edit & accept'
                                : 'Accept BDRC'
                              : `Save & accept (${PROVIDER_LABELS[leftSource]})`}
                          </button>
                          <button
                            type="button"
                            disabled={busy || !visionReady}
                            onClick={() => useVisionReading()}
                            className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                          >
                            Use {PROVIDER_LABELS[visionTab]} reading
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => openReviewWithAi()}
                            className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                          >
                            Run again
                          </button>
                          <label className="flex items-center gap-1.5 text-sm text-gray-600">
                            <span className="sr-only">Vision model</span>
                            <select
                              value={visionModelChoice}
                              disabled={busy}
                              onChange={e =>
                                setVisionModelChoice(
                                  e.target.value as VisionModelChoice
                                )
                              }
                              className="text-sm border border-gray-300 rounded px-2 py-1.5 bg-white disabled:opacity-50"
                            >
                              {VISION_MODEL_OPTIONS.map(opt => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </label>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => backToProof()}
                            className="px-3 py-2 text-sm border border-gray-300 rounded disabled:opacity-50"
                          >
                            Back to proof
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </section>
          </div>
        )}
      </div>

      {docxConfirmOpen && job && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="docx-confirm-title"
          onClick={e => {
            if (e.target === e.currentTarget) setDocxConfirmOpen(false)
          }}
        >
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
            <h2
              id="docx-confirm-title"
              className="text-lg font-semibold text-gray-900"
            >
              Download incomplete document?
            </h2>
            <p className="mt-3 text-sm text-gray-600 leading-relaxed">
              Only {acceptedCount} of {job.page_count} pages are accepted so
              far. Unaccepted pages will not be included in this DOCX.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDocxConfirmOpen(false)}
                className="px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  setDocxConfirmOpen(false)
                  startDocxDownload()
                }}
                className="px-3 py-2 text-sm font-medium text-white bg-blue-700 rounded hover:bg-blue-800"
              >
                Download anyway
              </button>
            </div>
          </div>
        </div>
      )}

      {imageLightbox && job && pageDetail && (
        <div
          className="fixed inset-0 z-50 flex flex-col bg-black/80"
          role="dialog"
          aria-modal="true"
          aria-label={`Page ${pageDetail.index} enlarged`}
        >
          <div className="flex items-center justify-between gap-3 px-4 py-3 text-white">
            <span className="text-sm">Page {pageDetail.index}</span>
            <button
              type="button"
              onClick={() => setImageLightbox(false)}
              className="px-3 py-1.5 text-sm border border-white/40 rounded hover:bg-white/10"
            >
              Close
            </button>
          </div>
          <div
            ref={lightboxViewportRef}
            className="flex-1 overflow-auto p-4"
            onClick={() => setImageLightbox(false)}
          >
            <div onClick={e => e.stopPropagation()}>
              <PageImage
                src={pageImageSrc}
                alt={`Page ${pageDetail.index} enlarged`}
                rotateDeg={viewRotateDeg}
                zoom={1}
                fitWidthPx={Math.min(lightboxViewportWidth, 1200)}
                className="block bg-white"
              />
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
