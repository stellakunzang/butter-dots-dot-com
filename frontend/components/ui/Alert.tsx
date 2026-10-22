import React from 'react'

type AlertTone = 'error' | 'success'

const TONES: Record<AlertTone, {box: string; title: string; body: string}> = {
  error: {
    box: 'border-red-200 bg-red-50',
    title: 'text-red-800',
    body: 'text-red-700',
  },
  success: {
    box: 'border-green-200 bg-green-50',
    title: 'text-green-800',
    body: 'text-green-700',
  },
}

export function Alert({
  tone,
  title,
  children,
  icon,
  className = '',
}: {
  tone: AlertTone
  title?: string
  children?: React.ReactNode
  icon?: React.ReactNode
  className?: string
}) {
  const style = TONES[tone]
  const body = (
    <>
      {title && <p className={`text-sm font-semibold ${style.title}`}>{title}</p>}
      {children && (
        <div className={`text-sm ${style.body}${title ? ' mt-1' : ''}`}>
          {children}
        </div>
      )}
    </>
  )

  return (
    <div className={`rounded-lg border p-4 ${style.box} ${className}`}>
      {icon ? (
        <div className="flex items-start gap-3">
          <span className="flex-shrink-0 mt-0.5">{icon}</span>
          <div className="min-w-0">{body}</div>
        </div>
      ) : (
        body
      )}
    </div>
  )
}
