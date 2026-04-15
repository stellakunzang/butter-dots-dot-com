import React from 'react'

interface PDFDownloadLinkProps {
  href: string
  label: string
  colorClass: string
}

export function PDFDownloadLink({href, label, colorClass}: PDFDownloadLinkProps) {
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
