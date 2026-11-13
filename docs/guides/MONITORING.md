# Production monitoring

Three layers, because each one misses something the others catch.

| Layer | Catches | Misses | Where it lives |
| --- | --- | --- | --- |
| External uptime monitor | The API down or hanging for minutes (the November 2026 outage) | A crash that recovers between checks | UptimeRobot or Better Stack account |
| Render notifications | Failed deploys; crashed or restarted instances where the plan offers those alerts. The Events tab records out-of-memory kills either way | Slow or hanging responses | Render dashboard |
| Sentry | What users actually hit: request timeouts, network failures, 5xx responses, unhandled API errors | An outage nobody visits during | `frontend/lib/monitoring.ts`, `backend/app/monitoring.py` |

A GitHub Actions workflow (`.github/workflows/uptime.yml`) also checks health every 15 minutes as a free backstop. GitHub can delay scheduled runs, so it does not replace the external monitor.

## 1. External uptime monitor

Use one free service. Either works:

- [UptimeRobot](https://uptimerobot.com)
- [Better Stack Uptime](https://betterstack.com/uptime)

Create an HTTP(S) monitor:

| Setting | Value |
| --- | --- |
| URL | `https://tibetan-spellchecker-api.onrender.com/api/v1/health` |
| Expected response | HTTP 200 |
| Check interval | The shortest the free plan allows (5 min or less) |
| Request timeout | 30 s |
| Alert after | 2 consecutive failures, so one slow response is not a page |
| Alert to | Email, plus SMS or the phone app if you want to hear about it away from the desk |

Side effect: regular checks keep a free-tier instance from going to sleep. On a paid instance that does not matter.

Test it once: pause the Render service (or point a test monitor at a URL that returns 404) and confirm the alert arrives.

## 2. Render notifications

In the Render dashboard, open the workspace's notification settings and turn on email (or Slack) for:

- failed deploys
- service failures, such as an instance crashing or being restarted

Check which events the current plan offers on that page. Whatever the alerts include, the service's **Events** tab records each restart. An out-of-memory kill shows there, which is how to confirm the cause after an alert.

## 3. Sentry

Off unless a DSN is set, so local development, tests and preview builds send nothing.

**What is sent.** Backend: unhandled exceptions, with no request bodies (`max_request_body_size="never"`), no user data, and no performance tracing. Frontend: only API failures users hit (timeouts, network failures, 5xx), tagged with the API path, failure kind and status. Never the text or PDF a user submitted.

**Setup.**

1. Create a free account at [sentry.io](https://sentry.io) and two projects: one Python (FastAPI) for the API, one Browser JavaScript for the site. Each gives you a DSN.
2. Render → the API service → Environment: set `SENTRY_DSN` to the API project's DSN. Optional: `SENTRY_ENVIRONMENT` (defaults to `production` on Render).
3. Netlify → Site configuration → Environment variables: set `NEXT_PUBLIC_SENTRY_DSN` to the browser project's DSN, and optionally `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production`. It is read at build time, so trigger a new deploy after setting it.
4. In each Sentry project, set an alert rule to email you on new issues (and, for the browser project, when an issue happens more than a few times an hour).

**What users see.** API calls now give up after a limit instead of waiting until the browser times out: 60 s for most requests, 5 min for OCR Assist page actions, 15 min for PDF uploads, which are processed inside the request. The user gets "The spell checker service did not respond in time. Please try again in a few minutes." The timeout is reported to Sentry.

**Not covered by Sentry.** An out-of-memory kill ends the process before it can report anything. Users who hit it surface as 502 or timeout reports from the browser, and the uptime monitor and Render notifications cover the rest.

## 4. GitHub Actions backstop

`.github/workflows/uptime.yml` runs every 15 minutes (and on demand from the Actions tab). It tries the health URL up to three times with a 60 s limit each, so a free-tier cold start does not fail it. A failed run emails whoever last edited the workflow's schedule, per GitHub's notification settings. Set a repository variable `API_HEALTH_URL` if the API moves.

GitHub disables scheduled workflows in a public repository after 60 days without activity. Re-enable it from the Actions tab if that happens.
