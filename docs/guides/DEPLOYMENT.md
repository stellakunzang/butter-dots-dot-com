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

## Backend: Render

1. New Web Service from the GitHub repository.
2. Root directory: `backend`. Runtime: Docker. Branch: `main`.
3. Environment:

| Variable | Value | Notes |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | `https://butterdots.com` | The public site origin |
| `PUBLIC_BASE_URL` | `https://api.butterdots.com` | Used in result links |
| `OCR_MODEL_NAME` | `Woodblock` | Also on disk: Woodblock-Stacks, Modern, Ume_Druma, Ume_Petsuk. The default in code is Woodblock. |

The first image build downloads the OCR models. Later builds reuse that layer.

`OCR_ASSIST_LOCAL` must stay unset on Render. The API refuses to start the
local OCR assist routes when that flag is set in production.
