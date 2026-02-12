import React, {useState, useEffect} from 'react'
import {Layout} from '@/components'
import {TextInput, ErrorDisplay} from '@/components/spellcheck'
import {checkText, SpellCheckResponse, APIError} from '@/lib/api'

export default function SpellCheckPage() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SpellCheckResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Clear results when text changes
  useEffect(() => {
    setResult(null)
    setError(null)
  }, [text])

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await checkText(text)
      setResult(response)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred. Please try again.')
      }
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setText('')
    setResult(null)
    setError(null)
  }

  return (
    <Layout
      title="Tibetan Spell Checker - Butter Dots Dot Com"
      description="Check Tibetan text for spelling errors using traditional grammar rules"
      showBackLink
    >
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-bold text-gray-900 mb-4">
            Tibetan Spell Checker
          </h1>
          <p className="text-lg text-gray-600 leading-relaxed">
            Paste Tibetan text below to check for spelling errors. The spell
            checker uses spelling rules to validate syllable structure including
            prefixes, superscripts, subscripts, vowels, and suffixes.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-800 mb-1">
                  Error
                </h4>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Input Text
            </h2>
            <TextInput
              value={text}
              onChange={setText}
              onSubmit={handleSubmit}
              onClear={handleClear}
              loading={loading}
              placeholder="བོད་ཡིག"
            />
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Results
            </h2>
            {result ? (
              <ErrorDisplay response={result} />
            ) : (
              <div className="flex items-center justify-center py-16 px-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center">
                  <svg
                    className="w-12 h-12 text-gray-400 mx-auto mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="text-gray-500 text-sm">
                    Enter text and click &quot;Check Spelling&quot; to see
                    results
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
