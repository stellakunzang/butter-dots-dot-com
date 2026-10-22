import React from 'react'
import {DownloadIcon} from '../ui/icons'

type DownloadVariant = 'pdf' | 'docx'

const VARIANT_CLASS: Record<DownloadVariant, string> = {
  pdf: 'bg-green-100 text-green-700 hover:bg-green-200',
  docx: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
}

interface PDFDownloadLinkProps {
  href: string
  label: string
  variant: DownloadVariant
}

export function PDFDownloadLink({href, label, variant}: PDFDownloadLinkProps) {
  return (
    <a
      href={href}
      download
      className={[
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
        VARIANT_CLASS[variant],
      ].join(' ')}
    >
      <DownloadIcon />
      {label}
    </a>
  )
}
