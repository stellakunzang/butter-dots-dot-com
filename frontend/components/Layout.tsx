import React from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { FeedbackButton } from './FeedbackButton'

interface LayoutProps {
  children: React.ReactNode
  title?: string
  description?: string
  showBackLink?: boolean
  backHref?: string
  backLabel?: string
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  title = 'Butter Dots',
  description = 'Butter Dots - small discs of butter formed in ice cold water',
  showBackLink = false,
  backHref = '/',
  backLabel = '← Back',
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <nav className="max-w-7xl mx-auto px-4 md:px-8 py-5 md:py-6 flex justify-between items-center gap-4">
          <Link
            href="/"
            className="font-serif text-xl md:text-2xl font-semibold text-gray-900 hover:text-gray-600 transition-colors shrink-0"
          >
            Butter Dots Dot Com
          </Link>
          <div className="flex flex-wrap justify-end gap-x-5 md:gap-x-6 gap-y-2">
            <Link
              href="/spellcheck"
              className="text-sm uppercase tracking-wider text-gray-500 hover:text-gray-900 font-medium transition-colors"
            >
              Spell Checker
            </Link>
            <Link
              href="/interactive-ocr"
              className="text-sm uppercase tracking-wider text-gray-500 hover:text-gray-900 font-medium transition-colors"
            >
              Interactive OCR
            </Link>
            <Link
              href="/learn"
              className="text-sm uppercase tracking-wider text-gray-500 hover:text-gray-900 font-medium transition-colors"
            >
              Learn
            </Link>
          </div>
        </nav>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-8 py-8">
        {showBackLink && (
          <Link
            href={backHref}
            className="inline-block text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-4 py-2 rounded-lg transition-all mb-8"
          >
            {backLabel}
          </Link>
        )}
        {children}
      </main>

      <footer className="bg-gray-50 border-t border-gray-200 py-8 text-center">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <p className="text-sm text-gray-500">
            Resources for the Orgyen Khandroling Sangha
          </p>
          <p className="text-sm text-gray-500 mt-2 space-x-4">
            <Link
              href="/learn"
              className="underline underline-offset-2 hover:text-gray-800 transition-colors"
            >
              Learn
            </Link>
            <Link
              href="/changelog"
              className="underline underline-offset-2 hover:text-gray-800 transition-colors"
            >
              Changelog
            </Link>
            <a
              href="https://github.com/stellakunzang/butter-dots-dot-com"
              className="underline underline-offset-2 hover:text-gray-800 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Source on GitHub
            </a>
          </p>
          <p className="text-xs text-gray-400 mt-2">
            © {new Date().getFullYear()} Butter Dots Dot Com
          </p>
        </div>
      </footer>

      <FeedbackButton />
    </div>
  )
}
