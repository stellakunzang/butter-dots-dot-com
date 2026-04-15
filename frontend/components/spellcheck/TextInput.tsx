import React from 'react'
import {Button} from '@/components'

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onClear?: () => void
  loading: boolean
  placeholder?: string
}

export const TextInput: React.FC<TextInputProps> = ({
  value,
  onChange,
  onSubmit,
  onClear,
  loading,
  placeholder = 'Paste Tibetan text here...',
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit()
  }

  const handleClear = () => {
    if (onClear) {
      onClear()
    } else {
      onChange('')
    }
  }

  const characterCount = value.length

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="w-full min-h-[300px] p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-y font-sans text-base disabled:bg-gray-50 disabled:cursor-not-allowed"
          style={{ fontFamily: 'Noto Sans Tibetan, sans-serif' }}
          aria-label="Tibetan text input"
        />
        <div className="absolute bottom-2 right-2 text-xs text-gray-400 bg-white px-2 py-1 rounded">
          {characterCount} characters
        </div>
      </div>

      <div className="flex gap-3 justify-end">
        {value.length > 0 && (
          <Button type="button" variant="outline" onClick={handleClear} disabled={loading}>
            Clear
          </Button>
        )}
        <Button
          type="submit"
          variant="primary"
          disabled={loading || value.trim().length === 0}
          className="min-w-[140px]"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
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
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Checking...
            </span>
          ) : (
            'Check Spelling'
          )}
        </Button>
      </div>
    </form>
  )
}
