import React from 'react'

interface CodeBlockProps {
  children: string
  language?: string
  inline?: boolean
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  children,
  language = 'bash',
  inline = false,
}) => {
  if (inline) {
    return (
      <code className="bg-gray-100 px-2 py-1 rounded font-mono text-sm text-pink-600 border border-gray-200">
        {children}
      </code>
    )
  }

  return (
    <div className="my-4 rounded-lg overflow-hidden bg-gray-900 shadow-sm">
      {language && (
        <div className="px-4 py-2 bg-gray-950 text-green-400 text-xs uppercase tracking-wide font-semibold">
          {language}
        </div>
      )}
      <pre className="m-0 p-6 overflow-x-auto">
        <code className="font-mono text-sm leading-relaxed text-gray-300">
          {children}
        </code>
      </pre>
    </div>
  )
}
