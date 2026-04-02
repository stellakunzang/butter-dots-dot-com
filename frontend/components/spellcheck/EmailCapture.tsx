import React, {useState} from 'react'

interface EmailCaptureProps {
  pageCount: number
  onSubmit: (email: string) => void
  onCancel: () => void
  loading: boolean
}

export function EmailCapture({
  pageCount,
  onSubmit,
  onCancel,
  loading,
}: EmailCaptureProps) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }
    setError('')
    onSubmit(email.trim())
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
      <h3 className="text-sm font-semibold text-amber-900 mb-1">
        Large document detected
      </h3>
      <p className="text-sm text-amber-800 mb-4">
        Your PDF has {pageCount} pages. Processing will happen in the background
        — enter your email and we&apos;ll send you the results when ready.
      </p>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label
            htmlFor="email-input"
            className="block text-xs font-medium text-gray-700 mb-1"
          >
            Email address
          </label>
          <input
            id="email-input"
            type="email"
            value={email}
            onChange={e => {
              setEmail(e.target.value)
              setError('')
            }}
            placeholder="you@example.com"
            disabled={loading}
            className={[
              'w-full rounded-md border px-3 py-2 text-sm',
              'focus:outline-none focus:ring-2 focus:ring-amber-400',
              error ? 'border-red-400' : 'border-gray-300',
              loading ? 'bg-gray-50 text-gray-400' : 'bg-white',
            ].join(' ')}
          />
          {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className={[
              'flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors',
              loading
                ? 'bg-amber-300 text-amber-700 cursor-not-allowed'
                : 'bg-amber-500 text-white hover:bg-amber-600',
            ].join(' ')}
          >
            {loading ? 'Queuing…' : 'Queue for processing'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
