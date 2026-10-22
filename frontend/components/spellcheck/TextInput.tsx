import React from 'react'
import {Button} from '@/components'
import {Spinner} from '../ui/Spinner'

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
              <Spinner className="h-4 w-4" />
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
