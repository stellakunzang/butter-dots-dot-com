import React, {useEffect, useState} from 'react'
import {getJobStatus, getResultURLs, JobStatusResponse} from '@/lib/api'

interface JobStatusProps {
  jobId: string
  email: string
  onCompleted: (status: JobStatusResponse) => void
}

const POLL_INTERVAL_MS = 3000

export function JobStatus({jobId, email, onCompleted}: JobStatusProps) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)
  const [pollError, setPollError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      try {
        const s = await getJobStatus(jobId)
        if (cancelled) return
        setStatus(s)

        if (s.status === 'completed') {
          onCompleted(s)
          return
        }
        if (s.status === 'failed') {
          return
        }

        setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        setPollError(err instanceof Error ? err.message : 'Polling failed')
      }
    }

    poll()
    return () => {
      cancelled = true
    }
  }, [jobId, onCompleted])

  if (pollError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        <strong>Polling error:</strong> {pollError}
      </div>
    )
  }

  if (!status) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Checking status…
      </div>
    )
  }

  if (status.status === 'failed') {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-sm font-semibold text-red-800 mb-1">Processing failed</p>
        <p className="text-sm text-red-700">{status.error_message || 'An unknown error occurred.'}</p>
      </div>
    )
  }

  const progressLabel =
    status.status === 'pending'
      ? 'Queued'
      : status.status === 'processing'
      ? `Processing… ${status.progress}%`
      : 'Complete'

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-5 space-y-4">
      <div>
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>{progressLabel}</span>
          <span>{status.progress}%</span>
        </div>
        <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
          <div
            className="h-full rounded-full bg-amber-400 transition-all duration-500"
            style={{width: `${status.progress}%`}}
          />
        </div>
      </div>

      <p className="text-xs text-gray-500">
        Results will be sent to <strong>{email}</strong> when ready.
        This page will update automatically.
      </p>

      {status.status === 'completed' && (
        <PDFResultLinks jobId={jobId} errorCount={status.error_count ?? 0} />
      )}
    </div>
  )
}

function PDFResultLinks({jobId, errorCount}: {jobId: string; errorCount: number}) {
  const urls = getResultURLs(jobId)

  return (
    <div className="space-y-2 pt-2 border-t border-gray-200">
      <p className="text-sm font-medium text-gray-800">
        {errorCount === 0
          ? 'No spelling errors found.'
          : `${errorCount} spelling error${errorCount === 1 ? '' : 's'} found.`}
      </p>
      <div className="flex flex-wrap gap-2">
        <DownloadButton href={urls.pdf} label="Annotated PDF" icon="pdf" />
        <DownloadButton href={urls.docx} label="Editable Word doc" icon="docx" />
        <DownloadButton href={urls.json} label="View errors (JSON)" icon="json" />
      </div>
    </div>
  )
}

function DownloadButton({
  href,
  label,
  icon,
}: {
  href: string
  label: string
  icon: 'pdf' | 'docx' | 'json'
}) {
  const colors = {
    pdf: 'bg-red-100 text-red-700 hover:bg-red-200',
    docx: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
    json: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
  }

  return (
    <a
      href={href}
      download
      className={[
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
        colors[icon],
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
