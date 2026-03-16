import fs from 'fs'
import path from 'path'

export type ChangeCategory =
  | 'Added'
  | 'Changed'
  | 'Deprecated'
  | 'Removed'
  | 'Fixed'
  | 'Security'

export interface CategoryBlock {
  type: ChangeCategory
  items: string[]
}

export interface VersionEntry {
  version: string
  date: string | null
  isUnreleased: boolean
  categories: CategoryBlock[]
}

const CHANGELOG_PATH = path.join(process.cwd(), '..', 'CHANGELOG.md')

const KNOWN_CATEGORIES = new Set<ChangeCategory>([
  'Added',
  'Changed',
  'Deprecated',
  'Removed',
  'Fixed',
  'Security',
])

function isChangeCategory(s: string): s is ChangeCategory {
  return KNOWN_CATEGORIES.has(s as ChangeCategory)
}

export function parseChangelog(): VersionEntry[] {
  const raw = fs.readFileSync(CHANGELOG_PATH, 'utf-8')
  const lines = raw.split('\n')

  const entries: VersionEntry[] = []
  let current: VersionEntry | null = null
  let currentCategory: CategoryBlock | null = null

  const finaliseCategory = () => {
    if (current && currentCategory && currentCategory.items.length > 0) {
      current.categories.push(currentCategory)
    }
    currentCategory = null
  }

  const finaliseEntry = () => {
    finaliseCategory()
    if (current && (current.isUnreleased || current.categories.length > 0)) {
      entries.push(current)
    }
    current = null
  }

  for (const line of lines) {
    // Version heading: ## [Unreleased] or ## [1.2.3] - 2024-01-01
    const versionMatch = line.match(/^## \[([^\]]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?/)
    if (versionMatch) {
      finaliseEntry()
      const label = versionMatch[1]
      const date = versionMatch[2] ?? null
      current = {
        version: label === 'Unreleased' ? 'Unreleased' : label,
        date,
        isUnreleased: label === 'Unreleased',
        categories: [],
      }
      continue
    }

    if (!current) continue

    // Category heading: ### Added
    const categoryMatch = line.match(/^### (.+)/)
    if (categoryMatch) {
      finaliseCategory()
      const label = categoryMatch[1].trim()
      if (isChangeCategory(label)) {
        currentCategory = {type: label, items: []}
      }
      continue
    }

    // List item
    const itemMatch = line.match(/^- (.+)/)
    if (itemMatch && currentCategory) {
      // Accumulate continuation lines by tracking whether we're mid-item
      currentCategory.items.push(itemMatch[1].trim())
      continue
    }

    // Continuation of a wrapped list item (indented)
    const continuationMatch = line.match(/^  (.+)/)
    if (continuationMatch && currentCategory && currentCategory.items.length > 0) {
      const last = currentCategory.items.length - 1
      currentCategory.items[last] += ' ' + continuationMatch[1].trim()
    }
  }

  finaliseEntry()

  return entries
}
