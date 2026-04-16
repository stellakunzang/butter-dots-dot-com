import React, { useState, useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'

type FeedbackType = 'bug' | 'feature'

interface FeedbackModalProps {
  open: boolean
  onClose: () => void
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({ open, onClose }) => {
  const [type, setType] = useState<FeedbackType>('bug')
  const [description, setDescription] = useState('')
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const overlayRef = useRef<HTMLDivElement>(null)
  const descriptionRef = useRef<HTMLTextAreaElement>(null)

  const resetForm = useCallback(() => {
    setType('bug')
    setDescription('')
    setEmail('')
    setStatus('idle')
    setErrorMessage('')
  }, [])

  useEffect(() => {
    if (open) {
      descriptionRef.current?.focus()
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  useEffect(() => {
    if (status === 'success') {
      const timer = setTimeout(() => {
        onClose()
        resetForm()
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [status, onClose, resetForm])

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) return

    setStatus('submitting')
    setErrorMessage('')

    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          description: description.trim(),
          ...(email.trim() && { email: email.trim() }),
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.error || 'Something went wrong')
      }

      setStatus('success')
    } catch (err) {
      setStatus('error')
      setErrorMessage(err instanceof Error ? err.message : 'Something went wrong')
    }
  }

  if (!open) return null

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-[100] flex items-end justify-end p-4 sm:items-center sm:justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 animate-in">
        {status === 'success' ? (
          <div className="text-center py-8">
            <div className="text-3xl mb-3">✓</div>
            <p className="text-gray-900 font-medium">Thanks for your feedback!</p>
            <p className="text-sm text-gray-500 mt-1">A GitHub issue has been created.</p>
          </div>
        ) : (
          <>
            <h2
              id="feedback-modal-title"
              className="text-lg font-semibold text-gray-900 mb-4"
            >
              Send Feedback
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setType('bug')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                    type === 'bug'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Bug Report
                </button>
                <button
                  type="button"
                  onClick={() => setType('feature')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                    type === 'feature'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Feature Request
                </button>
              </div>

              <div>
                <label htmlFor="feedback-description" className="sr-only">
                  Description
                </label>
                <textarea
                  ref={descriptionRef}
                  id="feedback-description"
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={
                    type === 'bug'
                      ? 'What happened? What did you expect?'
                      : 'What would you like to see?'
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-500 focus:ring-1 focus:ring-gray-500 resize-none"
                  required
                />
              </div>

              <div>
                <label htmlFor="feedback-email" className="sr-only">
                  Email (optional)
                </label>
                <input
                  id="feedback-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email for follow-up (optional)"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
                />
              </div>

              {status === 'error' && (
                <p className="text-sm text-red-600">{errorMessage}</p>
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={status === 'submitting' || !description.trim()}
                  className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {status === 'submitting' ? 'Sending…' : 'Submit'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>,
    document.body
  )
}
