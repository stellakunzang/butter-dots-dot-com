import React, {useState, useEffect} from 'react'
import {Layout, PageTitle} from '@/components'
import {TextInput, ErrorDisplay, PDFUpload, EmailCapture, JobStatus} from '@/components/spellcheck'
import {
  checkText,
  uploadPDF,
  getResultURLs,
  isSyncResponse,
  SpellCheckResponse,
  PDFUploadSyncResponse,
  JobStatusResponse,
  APIError,
} from '@/lib/api'

type Tab = 'text' | 'pdf'

type PDFState =
  | {phase: 'idle'}
  | {phase: 'file_selected'; file: File}
  | {phase: 'needs_email'; file: File; pageCount: number}
  | {phase: 'loading'; file: File}
  | {phase: 'sync_done'; result: PDFUploadSyncResponse}
  | {phase: 'async_queued'; jobId: string; email: string}
  | {phase: 'async_done'; jobId: string; errorCount: number}
  | {phase: 'error'; message: string}

export default function SpellCheckPage() {
  const [activeTab, setActiveTab] = useState<Tab>('text')

  // --- Text tab state ---
  const [text, setText] = useState('')
  const [textLoading, setTextLoading] = useState(false)
  const [textResult, setTextResult] = useState<SpellCheckResponse | null>(null)
  const [textError, setTextError] = useState<string | null>(null)

  // --- PDF tab state ---
  const [pdfState, setPdfState] = useState<PDFState>({phase: 'idle'})

  useEffect(() => {
    setTextResult(null)
    setTextError(null)
  }, [text])

  // ---- Text tab handlers ----

  const handleTextSubmit = async () => {
    setTextLoading(true)
    setTextError(null)
    try {
      const response = await checkText(text)
      setTextResult(response)
    } catch (err) {
      setTextError(err instanceof APIError ? err.message : 'An unexpected error occurred.')
      setTextResult(null)
    } finally {
      setTextLoading(false)
    }
  }

  const handleTextClear = () => {
    setText('')
    setTextResult(null)
    setTextError(null)
  }

  // ---- PDF tab handlers ----

  const handleFileSelect = (file: File) => {
    setPdfState({phase: 'file_selected', file})
  }

  const handlePDFSubmit = async (file: File, email?: string) => {
    setPdfState({phase: 'loading', file})
    try {
      const response = await uploadPDF(file, email)

      if (isSyncResponse(response)) {
        setPdfState({phase: 'sync_done', result: response})
      } else {
        // Async: page count too high, email required
        if (!email) {
          // Server told us it needs an email — show email capture
          setPdfState({phase: 'needs_email', file, pageCount: response.page_count})
        } else {
          setPdfState({phase: 'async_queued', jobId: response.job_id, email})
        }
      }
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Upload failed. Please try again.'
      // If the error mentions email requirement, show the email capture
      if (err instanceof APIError && err.status === 400 && msg.includes('email')) {
        const match = msg.match(/(\d+)\s+pages/)
        const pageCount = match ? parseInt(match[1]) : 0
        setPdfState({phase: 'needs_email', file, pageCount})
        return
      }
      setPdfState({phase: 'error', message: msg})
    }
  }

  const handleEmailSubmit = (email: string) => {
    if (pdfState.phase === 'needs_email') {
      handlePDFSubmit(pdfState.file, email)
    }
  }

  const handleAsyncCompleted = (status: JobStatusResponse) => {
    setPdfState({
      phase: 'async_done',
      jobId: status.job_id,
      errorCount: status.error_count ?? 0,
    })
  }

  const handlePDFReset = () => {
    setPdfState({phase: 'idle'})
  }

  return (
    <Layout
      title="Tibetan Spell Checker - Butter Dots Dot Com"
      description="Check Tibetan text for spelling errors using traditional grammar rules"
      showBackLink
    >
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <PageTitle>Tibetan Spell Checker</PageTitle>
          <p className="text-lg text-gray-600 leading-relaxed">
            Check Tibetan text or upload a PDF. The spell checker uses traditional
            grammar rules to validate syllable structure including prefixes,
            superscripts, subscripts, vowels, and suffixes.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-8">
          <TabButton
            active={activeTab === 'text'}
            onClick={() => setActiveTab('text')}
            label="Check text"
          />
          <TabButton
            active={activeTab === 'pdf'}
            onClick={() => setActiveTab('pdf')}
            label="Upload PDF"
          />
        </div>

        {/* Text tab */}
        {activeTab === 'text' && (
          <>
            {textError && <InlineError message={textError} />}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Input Text</h2>
                <TextInput
                  value={text}
                  onChange={setText}
                  onSubmit={handleTextSubmit}
                  onClear={handleTextClear}
                  loading={textLoading}
                  placeholder="བོད་ཡིག"
                />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Results</h2>
                {textResult ? (
                  <ErrorDisplay response={textResult} />
                ) : (
                  <EmptyResults label="Enter text and click &quot;Check Spelling&quot; to see results" />
                )}
              </div>
            </div>
          </>
        )}

        {/* PDF tab */}
        {activeTab === 'pdf' && (
          <div className="max-w-xl">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload a PDF</h2>
            <p className="text-sm text-gray-600 mb-6">
              Supports digital PDFs and scanned documents. Most PDFs process in
              seconds. Scanned pages and PDFs with unsupported font encoding may
              take 1–3 minutes.
            </p>

            {pdfState.phase === 'idle' || pdfState.phase === 'file_selected' ? (
              <div className="space-y-4">
                <PDFUpload
                  onFileSelect={handleFileSelect}
                  loading={false}
                  disabled={false}
                />
                {pdfState.phase === 'file_selected' && (
                  <button
                    onClick={() => handlePDFSubmit(pdfState.file)}
                    className="w-full rounded-md bg-amber-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
                  >
                    Check spelling
                  </button>
                )}
              </div>
            ) : pdfState.phase === 'loading' ? (
              <PDFUpload onFileSelect={() => {}} loading={true} disabled={true} />
            ) : pdfState.phase === 'needs_email' ? (
              <EmailCapture
                pageCount={pdfState.pageCount}
                onSubmit={handleEmailSubmit}
                onCancel={handlePDFReset}
                loading={false}
              />
            ) : pdfState.phase === 'sync_done' ? (
              <PDFSyncResults result={pdfState.result} onReset={handlePDFReset} />
            ) : pdfState.phase === 'async_queued' ? (
              <JobStatus
                jobId={pdfState.jobId}
                email={pdfState.email}
                onCompleted={handleAsyncCompleted}
              />
            ) : pdfState.phase === 'async_done' ? (
              <PDFAsyncDone
                jobId={pdfState.jobId}
                errorCount={pdfState.errorCount}
                onReset={handlePDFReset}
              />
            ) : pdfState.phase === 'error' ? (
              <div className="space-y-4">
                <InlineError message={pdfState.message} />
                <button
                  onClick={handlePDFReset}
                  className="text-sm text-amber-600 underline"
                >
                  Try again
                </button>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </Layout>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean
  onClick: () => void
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={[
        'px-5 py-2.5 text-sm font-medium border-b-2 transition-colors',
        active
          ? 'border-amber-500 text-amber-700'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
      ].join(' ')}
    >
      {label}
    </button>
  )
}

function InlineError({message}: {message: string}) {
  return (
    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start gap-3">
        <svg
          className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
        <p className="text-sm text-red-700">{message}</p>
      </div>
    </div>
  )
}

function EmptyResults({label}: {label: string}) {
  return (
    <div className="flex items-center justify-center py-16 px-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <div className="text-center">
        <svg
          className="w-12 h-12 text-gray-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-gray-500 text-sm" dangerouslySetInnerHTML={{__html: label}} />
      </div>
    </div>
  )
}

function PDFSyncResults({
  result,
  onReset,
}: {
  result: PDFUploadSyncResponse
  onReset: () => void
}) {
  const urls = getResultURLs(result.job_id)
  const hasErrors = result.error_count > 0

  return (
    <div className="space-y-5">
      <div className={`rounded-lg border p-4 ${hasErrors ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
        <p className={`text-sm font-semibold ${hasErrors ? 'text-red-800' : 'text-green-800'}`}>
          {hasErrors
            ? `${result.error_count} spelling error${result.error_count === 1 ? '' : 's'} found across ${result.page_count} page${result.page_count === 1 ? '' : 's'}.`
            : 'No spelling errors found.'}
        </p>
        {result.is_scanned && (
          <p className={`text-xs mt-1 ${hasErrors ? 'text-red-700' : 'text-green-700'}`}>
            Scanned document — results may vary based on image quality.
          </p>
        )}
      </div>

      {hasErrors && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Download results</p>
          <div className="flex flex-wrap gap-2">
            <ResultLink href={urls.pdf} label="Annotated PDF" colorClass="bg-green-100 text-green-700 hover:bg-green-200" />
            <ResultLink href={urls.docx} label="Editable Word doc" colorClass="bg-blue-100 text-blue-700 hover:bg-blue-200" />
          </div>
        </div>
      )}

      <button onClick={onReset} className="text-sm text-amber-600 underline">
        Upload another PDF
      </button>
    </div>
  )
}

function ResultLink({
  href,
  label,
  colorClass,
}: {
  href: string
  label: string
  colorClass: string
}) {
  return (
    <a
      href={href}
      download
      className={[
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
        colorClass,
      ].join(' ')}
    >
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
        />
      </svg>
      {label}
    </a>
  )
}

function PDFAsyncDone({
  jobId,
  errorCount,
  onReset,
}: {
  jobId: string
  errorCount: number
  onReset: () => void
}) {
  const urls = getResultURLs(jobId)
  const hasErrors = errorCount > 0

  return (
    <div className="space-y-4">
      <div className={`rounded-lg border p-4 ${hasErrors ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
        <p className={`text-sm font-semibold ${hasErrors ? 'text-red-800' : 'text-green-800'}`}>Processing complete</p>
        <p className={`text-sm ${hasErrors ? 'text-red-700' : 'text-green-700'}`}>
          {hasErrors
            ? `${errorCount} spelling error${errorCount === 1 ? '' : 's'} found.`
            : 'No spelling errors found.'}
        </p>
      </div>
      {hasErrors && (
        <div className="flex flex-wrap gap-2">
          <ResultLink href={urls.pdf} label="Annotated PDF" colorClass="bg-green-100 text-green-700 hover:bg-green-200" />
          <ResultLink href={urls.docx} label="Editable Word doc" colorClass="bg-blue-100 text-blue-700 hover:bg-blue-200" />
        </div>
      )}
      <button onClick={onReset} className="text-sm text-amber-600 underline">
        Upload another PDF
      </button>
    </div>
  )
}
