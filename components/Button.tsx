import React from 'react'
import Link from 'next/link'

interface ButtonProps {
  children: React.ReactNode
  href?: string
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'small' | 'medium' | 'large'
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
  download,
  target,
  rel,
  className = '',
}) => {
  // Base classes
  const baseClasses = 'inline-flex items-center justify-center gap-2 border-none rounded-lg font-semibold cursor-pointer transition-all'
  
  // Variant classes
  const variantClasses = {
    primary: 'bg-gradient-primary text-white shadow-md hover:shadow-lg hover:-translate-y-0.5',
    secondary: 'bg-gray-100 text-gray-800 border border-gray-200 hover:bg-white hover:border-primary-500',
    outline: 'bg-transparent text-primary-500 border-2 border-primary-500 hover:bg-primary-500 hover:text-white',
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
    <button onClick={onClick} className={classes}>
      {children}
    </button>
  )
}
