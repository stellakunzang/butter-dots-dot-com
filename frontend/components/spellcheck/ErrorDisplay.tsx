import React from 'react'
import { Card } from '@/components'
import { SpellCheckError, SpellCheckResponse } from '@/lib/api'

interface ErrorDisplayProps {
  response: SpellCheckResponse
}

const formatErrorType = (errorType: string): string => {
  return errorType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const severityClasses = {
    error: 'bg-red-100 text-red-800 border-red-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    critical: 'bg-red-200 text-red-900 border-red-300',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
  }

  const className =
    severityClasses[severity as keyof typeof severityClasses] ||
    severityClasses.error

  return (
    <span
      className={`inline-block px-2 py-1 text-xs font-medium rounded border ${className}`}
    >
      {severity.toUpperCase()}
    </span>
  )
}

const errorUnderlineClass = (severity: string): string => {
  if (severity === 'warning') return 'border-b-2 border-yellow-400 text-yellow-700 cursor-pointer'
  return 'border-b-2 border-red-500 text-red-700 cursor-pointer'
}

const AnnotatedText: React.FC<{ text: string; errors: SpellCheckError[] }> = ({
  text,
  errors,
}) => {
  // Filter to only spelling errors (not info messages)
  const spellingErrors = errors.filter(
    (e) => e.severity !== 'info' && e.position >= 0
  )

  if (spellingErrors.length === 0) {
    return (
      <div
        className="text-2xl leading-loose p-6 bg-white rounded-lg border border-gray-200"
        style={{ fontFamily: 'Jomolhari, serif' }}
      >
        {text}
      </div>
    )
  }

  // Create a map of error positions for quick lookup
  const errorMap = new Map<number, SpellCheckError>()
  spellingErrors.forEach((error) => {
    for (let i = 0; i < error.word.length; i++) {
      errorMap.set(error.position + i, error)
    }
  })

  // Render text with errors underlined (red = structural, yellow = unknown word)
  const chars = Array.from(text)
  const elements: React.ReactNode[] = []
  let currentErrorStart = -1
  let currentError: SpellCheckError | null = null

  for (let i = 0; i < chars.length; i++) {
    const error = errorMap.get(i)

    if (error && currentError !== error) {
      if (currentErrorStart >= 0 && currentError) {
        elements.push(
          <span
            key={`error-${currentErrorStart}`}
            className="relative inline-block group"
          >
            <span className={errorUnderlineClass(currentError.severity)}>
              {chars.slice(currentErrorStart, i).join('')}
            </span>
            <span className="invisible group-hover:visible absolute z-10 bottom-full left-0 mb-2 px-3 py-2 text-xs bg-gray-900 text-white rounded shadow-lg whitespace-nowrap">
              {formatErrorType(currentError.error_type)}
              {currentError.message && ` — ${currentError.message}`}
            </span>
          </span>
        )
      }
      currentErrorStart = i
      currentError = error
    } else if (!error && currentErrorStart >= 0 && currentError) {
      elements.push(
        <span
          key={`error-${currentErrorStart}`}
          className="relative inline-block group"
        >
          <span className={errorUnderlineClass(currentError.severity)}>
            {chars.slice(currentErrorStart, i).join('')}
          </span>
          <span className="invisible group-hover:visible absolute z-10 bottom-full left-0 mb-2 px-3 py-2 text-xs bg-gray-900 text-white rounded shadow-lg whitespace-nowrap">
            {formatErrorType(currentError.error_type)}
            {currentError.message && ` — ${currentError.message}`}
          </span>
        </span>
      )
      currentErrorStart = -1
      currentError = null
    }

    if (!error) {
      if (chars[i] === '\n') {
        elements.push(<br key={`br-${i}`} />)
      } else {
        elements.push(<span key={`char-${i}`}>{chars[i]}</span>)
      }
    }
  }

  if (currentErrorStart >= 0 && currentError) {
    elements.push(
      <span
        key={`error-${currentErrorStart}`}
        className="relative inline-block group"
      >
        <span className={errorUnderlineClass(currentError.severity)}>
          {chars.slice(currentErrorStart).join('')}
        </span>
        <span className="invisible group-hover:visible absolute z-10 bottom-full left-0 mb-2 px-3 py-2 text-xs bg-gray-900 text-white rounded shadow-lg whitespace-nowrap">
          {formatErrorType(currentError.error_type)}
          {currentError.message && ` — ${currentError.message}`}
        </span>
      </span>
    )
  }

  return (
    <div className="space-y-3">
      <div
        className="text-2xl leading-loose p-6 bg-white rounded-lg border border-gray-200"
        style={{ fontFamily: 'Jomolhari, serif' }}
      >
        {elements}
      </div>
      <div className="flex gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-4 border-b-2 border-red-500" />
          Structural error
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-4 border-b-2 border-yellow-400" />
          Not found in word corpus
        </span>
      </div>
    </div>
  )
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ response }) => {
  const { text, errors } = response

  // Separate structural errors, unknown-word warnings, and info messages
  const spellingErrors = errors.filter(
    (e) => e.severity !== 'info' && e.position >= 0
  )
  const structuralErrors = spellingErrors.filter((e) => e.severity !== 'warning')
  const unknownWordWarnings = spellingErrors.filter((e) => e.severity === 'warning')
  const infoMessages = errors.filter((e) => e.severity === 'info')

  // Success state: no spelling errors
  if (spellingErrors.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex flex-col items-center justify-center py-12 px-6 bg-green-50 rounded-lg border-2 border-green-200">
          <svg
            className="w-16 h-16 text-green-500 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-xl font-semibold text-green-800 mb-2">
            No spelling errors found!
          </h3>
          <p className="text-green-600 text-sm">
            Your Tibetan text has correct spelling.
          </p>
        </div>

        {infoMessages.length > 0 && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1 text-sm text-blue-700">
                {infoMessages[0].message}
              </div>
            </div>
          </div>
        )}

        <AnnotatedText text={text} errors={spellingErrors} />
      </div>
    )
  }

  // Error state: show annotated text with errors
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {structuralErrors.length > 0 && (
              <span className="text-red-700">
                {structuralErrors.length}{' '}
                {structuralErrors.length === 1 ? 'error' : 'errors'}
              </span>
            )}
            {structuralErrors.length > 0 && unknownWordWarnings.length > 0 && (
              <span className="text-gray-400 mx-2">/</span>
            )}
            {unknownWordWarnings.length > 0 && (
              <span className="text-yellow-700">
                {unknownWordWarnings.length}{' '}
                {unknownWordWarnings.length === 1 ? 'unknown word' : 'unknown words'}
              </span>
            )}
          </h3>
          <span className="text-xs text-gray-500">
            Hover over underlined text for details
          </span>
        </div>
      </div>

      {infoMessages.length > 0 && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1 text-sm text-blue-700">
              {infoMessages[0].message}
            </div>
          </div>
        </div>
      )}

      <AnnotatedText text={text} errors={spellingErrors} />

      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-700">Error Details:</h4>
        {spellingErrors.map((error, index) => (
          <Card
            key={`${error.position}-${index}`}
            variant="bordered"
            className={`my-0 border-l-4 ${error.severity === 'warning' ? 'border-l-yellow-400' : 'border-l-red-400'}`}
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="text-2xl font-semibold text-gray-900"
                      style={{ fontFamily: 'Jomolhari, serif' }}
                    >
                      {error.word}
                    </span>
                    <SeverityBadge severity={error.severity} />
                  </div>
                  <p className="text-sm text-gray-700 font-medium">
                    {formatErrorType(error.error_type)}
                  </p>
                  {error.message && (
                    <p className="text-sm text-gray-600 mt-1">
                      {error.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100">
                <div>
                  <span className="font-medium">Position:</span>{' '}
                  {error.position}
                </div>
                {error.component && (
                  <div>
                    <span className="font-medium">Component:</span>{' '}
                    {error.component}
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
