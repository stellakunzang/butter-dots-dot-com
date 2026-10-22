import React, {useEffect, useRef, useState} from 'react'
import {getJobStatus, getResultURLs, JobStatusResponse} from '@/lib/api'
import {Alert} from '../ui/Alert'
import {Spinner} from '../ui/Spinner'
import {PDFDownloadLink} from './PDFDownloadLink'

interface JobStatusProps {
  jobId: string
  email: string
  onCompleted: (status: JobStatusResponse) => void
}

const POLL_INTERVAL_MS = 3000

export function JobStatus({jobId, email, onCompleted}: JobStatusProps) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)
  const [pollError, setPollError] = useState<string | null>(null)
  const onCompletedRef = useRef(onCompleted)
  onCompletedRef.current = onCompleted

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    const poll = async () => {
      try {
        const s = await getJobStatus(jobId)
        if (cancelled) return
        setStatus(s)

        if (s.status === 'completed') {
          onCompletedRef.current(s)
          return
        }
        if (s.status === 'failed') {
          return
        }

        timer = setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        setPollError(err instanceof Error ? err.message : 'Polling failed')
      }
    }

    poll()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [jobId])

  if (pollError) {
    return (
      <Alert tone="error">
        <strong>Polling error:</strong> {pollError}
      </Alert>
    )
  }

  if (!status) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Spinner />
        Checking status…
      </div>
    )
  }

  if (status.status === 'failed') {
    return (
      <Alert tone="error" title="Processing failed">
        {status.error_message || 'An unknown error occurred.'}
      </Alert>
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
        Results will be sent to <strong>{email}</strong> when ready. This page
        will update automatically.
      </p>

      {status.status === 'completed' && (
        <PDFResultLinks jobId={jobId} errorCount={status.error_count ?? 0} />
      )}
    </div>
  )
}

function PDFResultLinks({
  jobId,
  errorCount,
}: {
  jobId: string
  errorCount: number
}) {
  const urls = getResultURLs(jobId)

  return (
    <div className="space-y-2 pt-2 border-t border-gray-200">
      <p className="text-sm font-medium text-gray-800">
        {errorCount === 0
          ? 'No spelling errors found.'
          : `${errorCount} spelling error${errorCount === 1 ? '' : 's'} found.`}
      </p>
      <div className="flex flex-wrap gap-2">
        <PDFDownloadLink href={urls.pdf} label="Annotated PDF" variant="pdf" />
        <PDFDownloadLink href={urls.docx} label="Editable Word doc" variant="docx" />
      </div>
    </div>
  )
}

