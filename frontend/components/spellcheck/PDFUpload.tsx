import React, {useCallback, useRef, useState} from 'react'

interface PDFUploadProps {
  onFileSelect: (file: File) => void
  loading: boolean
  disabled?: boolean
  selectedFile?: File | null
}

export function PDFUpload({onFileSelect, loading, disabled, selectedFile = null}: PDFUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        return
      }
      onFileSelect(file)
    },
    [onFileSelect]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [handleFile]
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const isDisabled = disabled || loading

  return (
    <div
      onDrop={handleDrop}
      onDragOver={e => {
        e.preventDefault()
        if (!isDisabled) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onClick={() => !isDisabled && inputRef.current?.click()}
      className={[
        'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed',
        'px-6 py-10 text-center cursor-pointer transition-colors',
        isDisabled
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
          : dragOver
          ? 'border-amber-400 bg-amber-50'
          : 'border-gray-300 bg-white hover:border-amber-300 hover:bg-amber-50',
      ].join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="sr-only"
        onChange={handleChange}
        disabled={isDisabled}
      />

      {loading ? (
        <>
          <svg
            className="w-10 h-10 text-amber-500 animate-spin mb-3"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          <p className="text-sm text-gray-500">Processing…</p>
          <p className="text-xs text-gray-400 mt-1">
            Processing may take 1–3 minutes for longer documents
          </p>
        </>
      ) : selectedFile ? (
        <>
          <svg
            className="w-10 h-10 text-amber-500 mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm font-medium text-gray-800">{selectedFile.name}</p>
          <p className="text-xs text-gray-500 mt-1">
            {(selectedFile.size / 1024 / 1024).toFixed(1)} MB — click to change
          </p>
        </>
      ) : (
        <>
          <svg
            className="w-10 h-10 text-gray-400 mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-sm font-medium text-gray-700">
            Drop a PDF here or{' '}
            <span className="text-amber-600 underline">browse</span>
          </p>
        </>
      )}
    </div>
  )
}
