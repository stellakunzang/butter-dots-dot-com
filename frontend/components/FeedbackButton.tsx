import React, { useState } from 'react'
import { FeedbackModal } from './FeedbackModal'

export const FeedbackButton: React.FC = () => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Send feedback"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-primary-500 text-white pl-4 pr-5 py-3 shadow-lg hover:bg-primary-600 hover:shadow-xl transition-all group"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-5 h-5"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <span className="text-sm font-medium">Feedback</span>
      </button>
      <FeedbackModal open={open} onClose={() => setOpen(false)} />
    </>
  )
}
