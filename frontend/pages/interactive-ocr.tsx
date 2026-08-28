import React, { useState } from 'react'
import type { NextPage } from 'next'
import Link from 'next/link'
import { Layout, PageTitle, SectionHeading } from '../components'

type FormStatus = 'idle' | 'submitting' | 'success' | 'error'

const InteractiveOcrPage: NextPage = () => {
  const [email, setEmail] = useState('')
  const [note, setNote] = useState('')
  const [status, setStatus] = useState<FormStatus>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please enter a valid email address.')
      setStatus('error')
      return
    }

    setStatus('submitting')
    setErrorMessage('')

    try {
      const res = await fetch('/api/ocr-waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          ...(note.trim() && { note: note.trim() }),
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.error || 'Something went wrong')
      }

      setStatus('success')
      setEmail('')
      setNote('')
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err instanceof Error ? err.message : 'Something went wrong'
      )
    }
  }

  return (
    <Layout
      title="Interactive OCR — Butter Dots"
      description="Per-page Tibetan OCR with quality scoring and human review. Request early access."
      showBackLink
    >
      <div className="mb-12 max-w-3xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Early Access
          </span>
        </div>
        <PageTitle>Interactive OCR</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          Convert a scanned Tibetan PDF into an editable Word document — one
          page at a time. Clean pages advance automatically; difficult pages
          get a focused review loop instead of a global tweak that breaks the
          rest of the document.
        </p>
      </div>

      <div className="max-w-3xl mx-auto space-y-14">
        <section>
          <SectionHeading className="mt-0">The problem</SectionHeading>
          <p className="text-lg text-gray-700 leading-relaxed">
            Traditional OCR pipelines apply one set of settings to an entire
            document. A page that needs a different model, rotation, or
            preprocessing either fails quietly or forces a retune that
            degrades every other page. For translators working from scans,
            that means hours of cleanup — or starting over.
          </p>
        </section>

        <section>
          <SectionHeading className="mt-0">How this works</SectionHeading>
          <ul className="space-y-4 text-lg text-gray-700 leading-relaxed list-none pl-0">
            <li className="flex gap-3">
              <span className="text-gray-400 font-medium tabular-nums shrink-0">
                1.
              </span>
              <span>
                Each page runs through{' '}
                <a
                  href="https://github.com/buda-base/tibetan-ocr-app"
                  className="text-gray-900 underline underline-offset-2 hover:text-gray-600"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  BDRC Tibetan OCR
                </a>{' '}
                with a quality score
                grounded in the same structural rules and word corpus as our{' '}
                <Link
                  href="/spellcheck"
                  className="text-gray-900 underline underline-offset-2 hover:text-gray-600"
                >
                  spell checker
                </Link>
                .
              </span>
            </li>
            <li className="flex gap-3">
              <span className="text-gray-400 font-medium tabular-nums shrink-0">
                2.
              </span>
              <span>
                Pages that look clean are accepted. Pages that don&apos;t stay
                open for retry: an AI diagnostician suggests page-local setting
                changes — never job-wide overrides.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="text-gray-400 font-medium tabular-nums shrink-0">
                3.
              </span>
              <span>
                When that isn&apos;t enough, an optional AI vision compare
                (Claude / Gemini) can propose an alternate reading — always as
                an explicit, per-page action, never a bulk auto-run.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="text-gray-400 font-medium tabular-nums shrink-0">
                4.
              </span>
              <span>
                Accepted pages export to a clean Word document with page
                markers, ready for translation work.
              </span>
            </li>
          </ul>
        </section>

        <section>
          <SectionHeading className="mt-0">Available today</SectionHeading>
          <p className="text-lg text-gray-700 leading-relaxed mb-4">
            Scanned-PDF OCR already powers the{' '}
            <Link
              href="/spellcheck"
              className="text-gray-900 underline underline-offset-2 hover:text-gray-600"
            >
              Upload PDF
            </Link>{' '}
            spellcheck path: extract text, flag structural and corpus issues,
            download an annotated PDF and editable DOCX. The interactive
            page-by-page assist loop, which leverages an AI diagnostician along
            with optional AI vision compare leveraging Claude and Gemini, is
            still in Beta testing.
          </p>
        </section>

        <section>
          <SectionHeading className="mt-0">Word corpus</SectionHeading>
          <p className="text-lg text-gray-700 leading-relaxed">
            Spellcheck and OCR quality scoring draw on a syllable inventory built
            from publicly available Tibetan lexicographic sources — including the{' '}
            <a
              href="https://github.com/MonlamIT/Tibetan-Lexicon"
              className="text-gray-900 underline underline-offset-2 hover:text-gray-600"
              target="_blank"
              rel="noopener noreferrer"
            >
              Monlam Tibetan Lexicon
            </a>{' '}
            (Apache-2.0), Botok word lists, and{' '}
            <a
              href="https://github.com/christiansteinert/tibetan-dictionary"
              className="text-gray-900 underline underline-offset-2 hover:text-gray-600"
              target="_blank"
              rel="noopener noreferrer"
            >
              Christian Steinert&apos;s public dictionary collection
            </a>
            . We use these as a reference inventory for validation on this site,
            not as a standalone dictionary we redistribute.
          </p>
        </section>

        <section
          id="waitlist"
          className="border border-gray-200 bg-white rounded-lg p-6 sm:p-8"
        >
          <h2 className="text-2xl font-serif text-gray-900 mb-2">
            Request access
          </h2>
          <p className="text-gray-600 mb-6 leading-relaxed">
            Leave your email if you&apos;d like early access, or if you&apos;re
            evaluating this for translation, archival, or interview purposes.
            We use this list to gauge interest and reach out when seats open.
          </p>

          {status === 'success' ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-5">
              <p className="text-emerald-900 font-medium">You&apos;re on the list.</p>
              <p className="text-sm text-emerald-800 mt-1">
                Thanks — we&apos;ll be in touch when interactive OCR opens up.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="ocr-waitlist-email"
                  className="block text-xs font-medium text-gray-700 mb-1"
                >
                  Email address
                </label>
                <input
                  id="ocr-waitlist-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={e => {
                    setEmail(e.target.value)
                    if (status === 'error') setStatus('idle')
                  }}
                  disabled={status === 'submitting'}
                  placeholder="you@example.com"
                  className={[
                    'w-full rounded-md border px-3 py-2 text-sm',
                    'focus:outline-none focus:ring-2 focus:ring-gray-400',
                    status === 'error' && errorMessage
                      ? 'border-red-400'
                      : 'border-gray-300',
                    status === 'submitting'
                      ? 'bg-gray-50 text-gray-400'
                      : 'bg-white',
                  ].join(' ')}
                />
              </div>

              <div>
                <label
                  htmlFor="ocr-waitlist-note"
                  className="block text-xs font-medium text-gray-700 mb-1"
                >
                  Anything we should know?{' '}
                  <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <textarea
                  id="ocr-waitlist-note"
                  rows={3}
                  value={note}
                  onChange={e => setNote(e.target.value)}
                  disabled={status === 'submitting'}
                  placeholder="e.g. working with woodblock scans, need for a specific archive project…"
                  className={[
                    'w-full rounded-md border border-gray-300 px-3 py-2 text-sm',
                    'focus:outline-none focus:ring-2 focus:ring-gray-400',
                    status === 'submitting'
                      ? 'bg-gray-50 text-gray-400'
                      : 'bg-white',
                  ].join(' ')}
                />
              </div>

              {status === 'error' && errorMessage && (
                <p className="text-sm text-red-600">{errorMessage}</p>
              )}

              <button
                type="submit"
                disabled={status === 'submitting'}
                className={[
                  'rounded-md px-5 py-2.5 text-sm font-medium transition-colors',
                  status === 'submitting'
                    ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    : 'bg-gray-900 text-white hover:bg-gray-700',
                ].join(' ')}
              >
                {status === 'submitting' ? 'Submitting…' : 'Join waitlist'}
              </button>
            </form>
          )}
        </section>
      </div>
    </Layout>
  )
}

export default InteractiveOcrPage
