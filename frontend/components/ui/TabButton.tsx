import React from 'react'

interface TabButtonProps {
  active: boolean
  onClick: () => void
  label: string
}

export function TabButton({active, onClick, label}: TabButtonProps) {
  return (
    <button
      type="button"
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
