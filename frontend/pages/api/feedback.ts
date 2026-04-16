import type { NextApiRequest, NextApiResponse } from 'next'

const GITHUB_TOKEN = process.env.GITHUB_FEEDBACK_TOKEN
const GITHUB_REPO = process.env.GITHUB_FEEDBACK_REPO || 'stellakunzang/butter-dots-dot-com'
const FORMSPREE_ENDPOINT = process.env.FORMSPREE_ENDPOINT

interface FeedbackBody {
  type: 'bug' | 'feature'
  description: string
  email?: string
}

function isValidBody(body: unknown): body is FeedbackBody {
  if (typeof body !== 'object' || body === null) return false
  const b = body as Record<string, unknown>
  if (b.type !== 'bug' && b.type !== 'feature') return false
  if (typeof b.description !== 'string' || b.description.trim().length === 0) return false
  if (b.email !== undefined && typeof b.email !== 'string') return false
  return true
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!GITHUB_TOKEN) {
    console.error('GITHUB_FEEDBACK_TOKEN is not configured')
    return res.status(500).json({ error: 'Feedback service is not configured' })
  }

  if (!isValidBody(req.body)) {
    return res.status(400).json({
      error: 'Invalid request. Provide type ("bug" | "feature") and a non-empty description.',
    })
  }

  const { type, description, email } = req.body
  const label = type === 'bug' ? 'bug' : 'enhancement'
  const title = `[${type === 'bug' ? 'Bug' : 'Feature Request'}] ${description.slice(0, 80)}`

  const issueBody = `${description}\n\n<sub>Submitted via the site feedback form</sub>`

  const [owner, repo] = GITHUB_REPO.split('/')

  const ghPromise = fetch(
    `https://api.github.com/repos/${owner}/${repo}/issues`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, body: issueBody, labels: [label] }),
    }
  )

  if (FORMSPREE_ENDPOINT && email) {
    fetch(FORMSPREE_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: type === 'bug' ? 'Bug Report' : 'Feature Request',
        description,
        email,
      }),
    }).catch((err) => console.error('Formspree error:', err))
  }

  const ghResponse = await ghPromise

  if (!ghResponse.ok) {
    const detail = await ghResponse.text()
    console.error('GitHub API error:', ghResponse.status, detail)
    return res.status(502).json({ error: 'Failed to create issue' })
  }

  const issue = await ghResponse.json()
  return res.status(201).json({ url: issue.html_url })
}
