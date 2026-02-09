import React from 'react'
import Head from 'next/head'
import Link from 'next/link'

interface LayoutProps {
  children: React.ReactNode
  title?: string
  description?: string
  showBackLink?: boolean
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  title = 'Butter Dots',
  description = 'Butter Dots - small discs of butter formed in ice cold water',
  showBackLink = false,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white/95 border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm">
        <nav className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
          <Link 
            href="/" 
            className="font-serif text-2xl font-semibold text-gray-800 hover:text-primary-500 transition-colors"
          >
            Butter Dots
          </Link>
          <div className="flex gap-8">
            <Link 
              href="/" 
              className="relative text-gray-600 hover:text-primary-500 font-medium transition-colors after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary-500 after:transition-all hover:after:w-full"
            >
              Home
            </Link>
            <Link 
              href="/resources" 
              className="relative text-gray-600 hover:text-primary-500 font-medium transition-colors after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary-500 after:transition-all hover:after:w-full"
            >
              Resources
            </Link>
          </div>
        </nav>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-8">
        {showBackLink && (
          <Link 
            href="/" 
            className="inline-block text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-4 py-2 rounded-lg transition-all mb-8"
          >
            ← Back
          </Link>
        )}
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200 py-8 text-center text-gray-500">
        <p>Made with butter and love</p>
      </footer>
    </div>
  )
}
