# Architecture Guide

This document describes the architecture and design system of the Butter Dots website.

## Overview

The project follows React/Next.js best practices with a component-based architecture using **Tailwind CSS** for styling. All design decisions are centralized in the Tailwind configuration to enable easy maintenance and consistent user experience across pages.

## Design System

### Tailwind CSS Configuration (`tailwind.config.js`)

All design tokens are defined in the Tailwind config:

- **Colors**: Custom color palettes (primary, accent, butter)
- **Typography**: Font families (sans, serif, mono)
- **Spacing**: Tailwind's default spacing scale
- **Gradients**: Custom gradient utilities

**To change the color scheme**, modify colors in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        500: '#667eea',  // Main primary color
        600: '#5568d3',  // Hover state
        // ...
      }
    }
  }
}
```

See [TAILWIND_GUIDE.md](./TAILWIND_GUIDE.md) for complete documentation.

## Component Architecture

### Core Components (`components/`)

All reusable UI components live in the `components/` directory:

#### `Layout.tsx`
- Wraps all pages with Tailwind utility classes
- Provides consistent header, navigation, and footer
- Handles meta tags and SEO
- Responsive design with `max-w-7xl` container
- Props:
  - `title`: Page title
  - `description`: Meta description
  - `showBackLink`: Display back navigation
  - `children`: Page content

#### `Button.tsx`
- Multi-purpose button/link component
- Variants: `primary`, `secondary`, `outline`
- Sizes: `small`, `medium`, `large`
- Automatically handles internal links (Next.js Link) vs external links
- Props:
  - `href`: Link destination (optional)
  - `onClick`: Click handler for buttons (optional)
  - `variant`: Style variant
  - `size`: Size variant
  - `download`: For downloadable files
  - `target`, `rel`: For external links

#### `Section.tsx`
- Page section container with optional title
- Variants: `default`, `highlight`, `minimal`
- Provides consistent spacing and styling
- Props:
  - `title`: Optional section heading
  - `variant`: Style variant
  - `children`: Section content

#### `Card.tsx`
- Container for grouped content
- Variants: `default`, `bordered`, `elevated`
- Props:
  - `title`: Optional card heading
  - `variant`: Style variant
  - `children`: Card content

#### `CodeBlock.tsx`
- Displays code snippets or commands
- Two modes: inline and block
- Props:
  - `children`: Code content (string)
  - `language`: Syntax language (default: bash)
  - `inline`: Render as inline code (boolean)

### Component Index (`components/index.ts`)

All components are exported from a single index file for clean imports:

```typescript
import { Layout, Button, Section } from '../components'
```

## Page Structure

### Pages (`pages/`)

Pages use the Layout component and compose UI from reusable components:

```tsx
import { Layout, Section, Button } from '../components'

const MyPage = () => {
  return (
    <Layout title="My Page" description="Page description">
      <Section title="Section Title">
        <p>Content here</p>
        <Button href="/somewhere">Click Me</Button>
      </Section>
    </Layout>
  )
}
```

### Page-Specific Styles

Pages should have minimal CSS modules for unique styling needs only. Most styling comes from components and global CSS variables.

**Example**: `Home.module.css` only contains styles specific to the home page hero section, not general layout or button styles.

## Styling Guidelines

### Tailwind CSS Approach

1. **Utility Classes in Components**
   - All styling done with Tailwind utilities
   - No CSS modules needed
   - Variants handled with JavaScript objects

2. **Tailwind Config** (`tailwind.config.js`)
   - Custom colors, fonts, spacing
   - Theme extensions
   - Plugin configuration

3. **Global Styles** (`styles/globals.css`)
   - Tailwind directives only
   - Base layer for HTML elements
   - Minimal custom CSS

### Best Practices

1. **Use Theme Colors**: Reference configured colors
   ```tsx
   {/* Good - Uses theme */}
   <div className="bg-primary-500 text-white">
   
   {/* Avoid - Arbitrary values */}
   <div className="bg-[#667eea] text-[#ffffff]">
   ```

2. **Component Composition**: Build complex UIs from simple components
   ```tsx
   {/* Good - Reusable components */}
   <Section title="My Section">
     <Card title="My Card">
       <Button href="/link">Action</Button>
     </Card>
   </Section>
   
   {/* Avoid - Duplicating utility classes */}
   <div className="my-8 p-8 bg-white rounded-xl shadow-sm">
     <div className="p-6 rounded-lg my-4 bg-white shadow-md">
       <a className="inline-flex items-center...">Action</a>
     </div>
   </div>
   ```

3. **Single Source of Truth**: Design decisions live in Tailwind config
   - Colors: `tailwind.config.js` theme.colors
   - Spacing: Tailwind's spacing scale
   - Typography: `tailwind.config.js` theme.fontFamily
   - Component variants: JavaScript objects in components

4. **Props Over Variants**: When adding features
   - First: Try adding a prop to existing component
   - Then: Add a variant if it's a distinct style
   - Last: Create new component if truly unique

## Adding New Features

### Adding a New Page

1. Create page file in `pages/`:
   ```tsx
   import { Layout, Section, Button } from '../components'
   
   const NewPage = () => {
     return (
       <Layout title="New Page" description="Description">
         {/* Page content */}
       </Layout>
     )
   }
   
   export default NewPage
   ```

2. Add navigation link in `Layout.tsx`:
   ```tsx
   <Link href="/new-page" className={styles.navLink}>
     New Page
   </Link>
   ```

3. Create minimal CSS module if needed:
   ```css
   /* styles/NewPage.module.css */
   .uniqueLayout {
     /* Only page-specific styles */
   }
   ```

### Adding a New Component

1. Create component file in `components/`:
   ```tsx
   import React from 'react'
   import styles from '../styles/NewComponent.module.css'
   
   interface NewComponentProps {
     // Define props
   }
   
   export const NewComponent: React.FC<NewComponentProps> = (props) => {
     return (
       <div className={styles.container}>
         {/* Component markup */}
       </div>
     )
   }
   ```

2. Create CSS module in `styles/`:
   ```css
   /* styles/NewComponent.module.css */
   .container {
     /* Use CSS variables */
     color: var(--text-primary);
     padding: var(--spacing-md);
   }
   ```

3. Export from `components/index.ts`:
   ```typescript
   export { NewComponent } from './NewComponent'
   ```

### Modifying the Design System

To change colors, spacing, or typography across the entire site:

1. Open `tailwind.config.js`
2. Modify theme colors/fonts/etc.
3. Restart dev server
4. Changes apply everywhere automatically

**Example**: Changing the accent color

```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary: {
        500: '#ff6b6b',  // New color
        600: '#ee5a52',  // New hover
      }
    }
  }
}
```

All components using `bg-primary-500` or `text-primary-500` update automatically.

## File Organization

```
butter-dots-dot-com/
├── components/           # Reusable components (Tailwind styled)
│   ├── Layout.tsx
│   ├── Button.tsx
│   ├── Section.tsx
│   ├── Card.tsx
│   ├── CodeBlock.tsx
│   └── index.ts         # Component exports
├── pages/               # Next.js pages
│   ├── index.tsx        # Home page
│   ├── resources.tsx    # Resources page
│   └── _app.tsx         # App wrapper (Next.js)
├── styles/              # Styles
│   └── globals.css      # Tailwind directives & base styles
├── public/              # Static assets
│   ├── butterdots.jpg
│   └── install-tibetan-fonts.sh
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
└── TAILWIND_GUIDE.md    # Tailwind documentation
```

## Responsive Design

All components are mobile-responsive by default. Media queries are included in component CSS modules:

```css
@media (max-width: 768px) {
  /* Mobile adjustments */
}
```

## TypeScript

All components use TypeScript with proper interfaces:

```typescript
interface ComponentProps {
  requiredProp: string
  optionalProp?: boolean
  children?: React.ReactNode
}

export const Component: React.FC<ComponentProps> = ({ ... }) => { ... }
```

## Summary

- ✅ **Tailwind CSS**: Utility-first styling for rapid development
- ✅ **Centralized Design**: All design tokens in `tailwind.config.js`
- ✅ **Reusable Components**: Build pages from composable pieces
- ✅ **Type Safety**: TypeScript interfaces for all components
- ✅ **Maintainable**: Change design in one place, applies everywhere
- ✅ **Scalable**: Easy to add new pages and components
- ✅ **Best Practices**: React/Next.js + Tailwind patterns throughout

For complete Tailwind documentation, see [TAILWIND_GUIDE.md](./TAILWIND_GUIDE.md).
