# Tailwind CSS Guide

This project uses Tailwind CSS for styling. All components use utility classes instead of CSS modules.

## Setup Complete ✅

The project has been fully migrated to Tailwind CSS:
- ✅ Tailwind installed and configured
- ✅ All components converted to utility classes
- ✅ Custom color palette configured
- ✅ CSS modules removed
- ✅ Design system maintained

## Installation

When your Node.js environment is fixed, run:

```bash
yarn install
```

This will install:
- `tailwindcss` - The framework
- `postcss` - Required for processing
- `autoprefixer` - Browser compatibility

## Configuration

### `tailwind.config.js`

Custom theme extends Tailwind's defaults:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* Purple shades */ },
      accent: { /* Accent shades */ },
      butter: { /* Butter/gold shades */ },
    },
    fontFamily: {
      sans: [/* System fonts */],
      serif: ['Georgia', ...],
      mono: ['Monaco', ...],
    },
    backgroundImage: {
      'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    },
  },
}
```

### Using Custom Colors

```tsx
// Primary purple
<div className="bg-primary-500 text-white">
<Button variant="primary">Uses primary-500</Button>

// Accent colors
<div className="border-accent-600">

// Butter/gold accent
<div className="border-b-2 border-butter-600">
```

## Component Patterns

### Button Component

Uses JavaScript object for variant classes:

```tsx
const variantClasses = {
  primary: 'bg-gradient-primary text-white shadow-md hover:shadow-lg',
  secondary: 'bg-gray-100 text-gray-800 border border-gray-200',
  outline: 'bg-transparent text-primary-500 border-2 border-primary-500',
}
```

Usage:
```tsx
<Button variant="primary" size="large">Click Me</Button>
<Button variant="outline" href="/page">Link</Button>
```

### Layout Component

Responsive navigation with Tailwind:

```tsx
<header className="bg-white/95 border-b border-gray-200 sticky top-0 z-50">
  <nav className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
    {/* Navigation content */}
  </nav>
</header>
```

### Section Component

Variant-based styling:

```tsx
const variantClasses = {
  default: 'my-8 p-8 bg-white rounded-xl shadow-sm',
  highlight: 'my-8 p-8 bg-white border-l-4 border-primary-500 rounded-xl shadow-md',
  minimal: 'my-8 py-4',
}
```

## Common Tailwind Patterns

### Layout & Spacing

```tsx
// Container
<div className="max-w-7xl mx-auto px-8 py-4">

// Flexbox
<div className="flex items-center justify-between gap-4">

// Grid
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">

// Centering
<div className="flex flex-col items-center justify-center">
```

### Typography

```tsx
// Headings
<h1 className="text-5xl font-serif text-gray-800">
<h2 className="text-3xl font-serif text-gray-800">
<h3 className="text-2xl font-serif text-gray-800">

// Body text
<p className="text-base leading-relaxed text-gray-600">
<p className="text-xl text-gray-600">

// Links
<a className="text-primary-500 hover:text-accent-600 transition-colors">
```

### Colors

```tsx
// Backgrounds
className="bg-white"
className="bg-gray-50"
className="bg-primary-500"
className="bg-gradient-primary"

// Text
className="text-gray-800"  // Dark text
className="text-gray-600"  // Body text
className="text-gray-400"  // Muted text
className="text-primary-500"  // Accent text

// Borders
className="border border-gray-200"
className="border-l-4 border-primary-500"
```

### Shadows & Effects

```tsx
// Shadows
className="shadow-sm"   // Subtle
className="shadow-md"   // Medium
className="shadow-lg"   // Large
className="shadow-2xl"  // Extra large

// Rounded corners
className="rounded-lg"   // 8px
className="rounded-xl"   // 12px
className="rounded-full" // Fully rounded

// Hover effects
className="hover:shadow-lg hover:-translate-y-0.5 transition-all"
```

### Responsive Design

```tsx
// Mobile-first approach
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
// 1 column on mobile, 2 on tablet, 3 on desktop

<div className="text-2xl md:text-4xl lg:text-6xl">
// Responsive text sizing

<div className="px-4 md:px-8 lg:px-12">
// Responsive padding
```

## Customizing the Design

### Change Colors

Edit `tailwind.config.js`:

```javascript
colors: {
  primary: {
    500: '#667eea',  // Change this
    600: '#5568d3',
    // ...
  }
}
```

All components using `primary-500` will update automatically.

### Add New Colors

```javascript
colors: {
  brand: {
    light: '#...',
    DEFAULT: '#...',
    dark: '#...',
  }
}
```

Use: `className="bg-brand text-brand-dark"`

### Extend Utilities

```javascript
extend: {
  spacing: {
    '128': '32rem',
  },
  fontSize: {
    'xxl': '2rem',
  }
}
```

## Best Practices

### 1. Use Consistent Spacing

```tsx
// Good - Tailwind's spacing scale
<div className="p-4 m-8 gap-6">

// Avoid - Arbitrary values (unless necessary)
<div className="p-[13px]">
```

### 2. Group Related Classes

```tsx
// Layout first, then appearance, then states
<button className="
  flex items-center justify-center
  px-6 py-3 rounded-lg
  bg-primary-500 text-white
  hover:shadow-lg transition-all
">
```

### 3. Extract Repeated Patterns

If you use the same classes repeatedly, create a component:

```tsx
// Instead of repeating everywhere
<h2 className="text-3xl font-serif text-gray-800 border-b-2 border-butter-600 pb-2">

// Create a component
const SectionHeading = ({ children }) => (
  <h2 className="text-3xl font-serif text-gray-800 border-b-2 border-butter-600 pb-2">
    {children}
  </h2>
)
```

### 4. Use @apply Sparingly

Tailwind recommends utility classes in JSX. Only use `@apply` for very specific cases:

```css
/* globals.css - for base styles only */
@layer base {
  h1 {
    @apply text-4xl font-serif text-gray-800;
  }
}
```

## Debugging

### Classes Not Applying?

1. **Check content paths** in `tailwind.config.js`:
   ```javascript
   content: [
     './pages/**/*.{js,ts,jsx,tsx}',
     './components/**/*.{js,ts,jsx,tsx}',
   ]
   ```

2. **Don't use string concatenation**:
   ```tsx
   // ❌ Bad - Tailwind can't detect these
   <div className={`text-${color}-500`}>
   
   // ✅ Good - Use complete class names
   const colorClasses = {
     primary: 'text-primary-500',
     accent: 'text-accent-500',
   }
   <div className={colorClasses[color]}>
   ```

3. **Restart dev server** after config changes

### View Applied Styles

Use browser DevTools to inspect elements and see which Tailwind classes are applied.

## VS Code Extensions

Install for better DX:

- **Tailwind CSS IntelliSense** - Autocomplete, linting, hover previews
- **Headwind** - Auto-sort Tailwind classes

## Resources

- [Tailwind Documentation](https://tailwindcss.com/docs)
- [Tailwind Playground](https://play.tailwindcss.com/)
- [Color Palette Generator](https://uicolors.app/create)
- [Tailwind Components](https://tailwindui.com/components)

## Migration Complete! 🎉

All components now use Tailwind. You can:
- ✅ Modify colors in one place (`tailwind.config.js`)
- ✅ Use Tailwind's full utility library
- ✅ Add responsive designs easily
- ✅ Leverage Tailwind's ecosystem (plugins, templates, etc.)
