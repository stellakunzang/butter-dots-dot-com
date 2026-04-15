import React from 'react'

interface ResetLinkProps {
  onClick: () => void
  children: React.ReactNode
}

export function ResetLink({onClick, children}: ResetLinkProps) {
  return (
    <button type="button" onClick={onClick} className="text-sm text-amber-600 underline">
      {children}
    </button>
  )
}
