import React from 'react'
import Link from 'next/link'

interface ButtonProps {
  children: React.ReactNode
  href?: string
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  download?: boolean | string
  target?: string
  rel?: string
  className?: string
}

export const Button: React.FC<ButtonProps> = ({
  children,
  href,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  type = 'button',
  download,
  target,
  rel,
  className = '',
}) => {
  // Base classes
  const baseClasses = 'inline-flex items-center justify-center gap-2 border-none rounded-lg font-semibold cursor-pointer transition-all disabled:opacity-50 disabled:cursor-not-allowed'
  
  // Variant classes
  const variantClasses = {
    primary: 'bg-gray-900 text-white shadow-md hover:shadow-xl hover:bg-gray-800 hover:-translate-y-0.5',
    secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 shadow-sm',
    outline: 'bg-transparent text-gray-700 border-2 border-gray-300 hover:bg-gray-900 hover:text-white hover:border-gray-900',
  }
  
  // Size classes
  const sizeClasses = {
    small: 'px-4 py-2 text-sm',
    medium: 'px-6 py-3 text-base',
    large: 'px-8 py-4 text-lg',
  }
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`

  if (href) {
    if (href.startsWith('http') || href.startsWith('//')) {
      return (
        <a
          href={href}
          className={classes}
          download={download}
          target={target}
          rel={rel}
        >
          {children}
        </a>
      )
    }

    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    )
  }

  return (
    <button onClick={onClick} className={classes} disabled={disabled} type={type}>
      {children}
    </button>
  )
}
