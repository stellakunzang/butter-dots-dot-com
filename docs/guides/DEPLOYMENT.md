# Deployment

Pushing to `main` runs the test workflow. On a successful push to `main`,
that workflow calls the Render deploy hook (`RENDER_DEPLOY_HOOK_URL`).

The notes below are the original host setup. The frontend was configured on
Netlify and the backend on Render.

## Frontend: Netlify

1. Import the GitHub repository.
2. Base directory: `frontend`.
3. Build command: `yarn build`.
4. Publish directory: `frontend/.next`.
5. Environment: `NEXT_PUBLIC_API_URL` (the API origin) and, optionally, `NEXT_PUBLIC_SENTRY_DSN` for error reporting. Both are read at build time.

## Backend: Render

1. New Web Service from the GitHub repository.
2. Root directory: `backend`. Runtime: Docker. Branch: `main`.
3. Environment:

| Variable | Value | Notes |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | `https://butterdots.com` | The public site origin |
| `PUBLIC_BASE_URL` | `https://api.butterdots.com` | Used in result links |
| `OCR_MODEL_NAME` | `Woodblock` | Also on disk: Woodblock-Stacks, Modern, Ume_Druma, Ume_Petsuk. The default in code is Woodblock. |
| `SENTRY_DSN` | the API project's DSN | Optional. Error reporting; off when unset. See [MONITORING.md](MONITORING.md). |

The first image build downloads the OCR models. Later builds reuse that layer.

**Instance size.** Scanned-PDF OCR loads the BDRC models and holds about 580 MB, so the API needs more than 512 MB. The free and Starter plans run out of memory on the first scanned upload and restart. Use Standard (2 GB) or larger. See [PRODUCTION_HOSTING.md](../planning/PRODUCTION_HOSTING.md).

**Monitoring.** Uptime monitor, Render notifications and Sentry: [MONITORING.md](MONITORING.md).

`OCR_ASSIST_LOCAL` must stay unset on Render. The API refuses to start the
local OCR assist routes when that flag is set in production.
