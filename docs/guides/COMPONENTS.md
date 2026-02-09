# Component Reference

Quick reference guide for all available components.

## Layout

Wraps all pages with consistent header, navigation, and footer.

```tsx
import { Layout } from '../components'

<Layout
  title="Page Title"              // Browser tab title
  description="Page description"  // Meta description
  showBackLink={false}            // Show back button (optional)
>
  {/* Page content */}
</Layout>
```

## Button

Multi-purpose button and link component.

```tsx
import { Button } from '../components'

// Primary button (default)
<Button href="/page">Click Me</Button>

// Variants
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>

// Sizes
<Button size="small">Small</Button>
<Button size="medium">Medium</Button>  {/* default */}
<Button size="large">Large</Button>

// External link
<Button 
  href="https://example.com" 
  target="_blank" 
  rel="noopener noreferrer"
>
  External Link
</Button>

// Download button
<Button 
  href="/file.pdf" 
  download="filename.pdf"
>
  Download
</Button>

// Click handler (not a link)
<Button onClick={() => console.log('clicked')}>
  Click Handler
</Button>
```

## Section

Container for page sections with optional title.

```tsx
import { Section } from '../components'

// With title
<Section title="Section Title">
  <p>Content here...</p>
</Section>

// Variants
<Section variant="default">Default background</Section>
<Section variant="highlight">Highlighted with border</Section>
<Section variant="minimal">No background</Section>

// Without title
<Section>
  <p>Just content...</p>
</Section>
```

## Card

Container for grouped content.

```tsx
import { Card } from '../components'

// With title
<Card title="Card Title">
  <p>Card content...</p>
</Card>

// Variants
<Card variant="default">Gray background</Card>
<Card variant="bordered">White with border</Card>
<Card variant="elevated">White with shadow</Card>

// Without title
<Card>
  <p>Just content...</p>
</Card>
```

## CodeBlock

Display code snippets or commands.

```tsx
import { CodeBlock } from '../components'

// Block code
<CodeBlock language="bash">
{`cd ~/Downloads
chmod +x script.sh
./script.sh`}
</CodeBlock>

// Inline code
<CodeBlock inline>npm install</CodeBlock>

// Other languages
<CodeBlock language="javascript">
{`const hello = "world";`}
</CodeBlock>

<CodeBlock language="typescript">
{`interface Props {
  name: string;
}`}
</CodeBlock>
```

## Composing Components

Components are designed to work together:

```tsx
import { Layout, Section, Card, Button, CodeBlock } from '../components'

const MyPage = () => {
  return (
    <Layout title="My Page" description="Page description">
      <Section title="Getting Started" variant="highlight">
        <p>Welcome to the page!</p>
        <Button href="/next-page">Continue</Button>
      </Section>

      <Section title="Installation">
        <Card title="Step 1" variant="bordered">
          <p>First, download the file.</p>
          <Button href="/file.sh" download variant="primary">
            Download
          </Button>
        </Card>

        <Card title="Step 2" variant="bordered">
          <p>Then run this command:</p>
          <CodeBlock language="bash">chmod +x file.sh</CodeBlock>
        </Card>
      </Section>

      <Section title="Documentation" variant="minimal">
        <ul>
          <li><a href="https://docs.example.com">View Docs</a></li>
          <li><a href="https://github.com">Source Code</a></li>
        </ul>
      </Section>
    </Layout>
  )
}
```

## Styling Components

### Using CSS Variables

All components reference global CSS variables defined in `styles/globals.css`:

```css
/* In your component CSS module */
.myElement {
  color: var(--text-primary);      /* Use design tokens */
  background: var(--bg-secondary);
  padding: 1rem;
  border-radius: var(--radius-md);
}
```

### Available CSS Variables

**Colors:**
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
- `--text-primary`, `--text-secondary`, `--text-tertiary`
- `--accent-primary`, `--accent-secondary`, `--accent-hover`
- `--border-color`

**Typography:**
- `--font-sans`, `--font-serif`, `--font-mono`

**Spacing:**
- `--radius-sm`, `--radius-md`, `--radius-lg`
- `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- `--max-width` (for page content)

**Special:**
- `--gradient-primary` (purple gradient)

### Adding Custom Props

If you need to pass custom className:

```tsx
<Button className="myCustomClass" href="/page">
  Custom Styled Button
</Button>

<Section className="myCustomSection" title="Title">
  Content
</Section>
```

All components accept a `className` prop that will be merged with component styles.

## TypeScript Support

All components are fully typed:

```tsx
// Button props
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

// Layout props
interface LayoutProps {
  children: React.ReactNode
  title?: string
  description?: string
  showBackLink?: boolean
}

// Section props
interface SectionProps {
  children: React.ReactNode
  title?: string
  variant?: 'default' | 'highlight' | 'minimal'
  className?: string
}

// Card props
interface CardProps {
  children: React.ReactNode
  title?: string
  variant?: 'default' | 'bordered' | 'elevated'
  className?: string
}

// CodeBlock props
interface CodeBlockProps {
  children: string
  language?: string
  inline?: boolean
}
```

## Best Practices

1. **Always use Layout**: Every page should be wrapped in `<Layout>`
2. **Compose, don't duplicate**: Use existing components instead of custom divs
3. **Reference CSS variables**: Never hardcode colors or spacing
4. **Keep page CSS minimal**: Most styling comes from components
5. **Use TypeScript**: Leverage type checking for props
6. **Semantic HTML**: Components render semantic elements (nav, section, article, etc.)
7. **Accessibility**: Components include ARIA attributes where needed

## Examples from Existing Pages

See these files for real-world examples:
- `pages/index.tsx` - Home page using Layout, Button
- `pages/resources.tsx` - Complex page using all components
