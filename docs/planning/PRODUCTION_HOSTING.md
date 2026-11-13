# Production hosting

**Status:** Decided 10 Nov 2026: Render Standard, no managed database. The instance upgrade and the word-list change are not done yet (see "Next steps").
**Monitoring:** [MONITORING.md](../guides/MONITORING.md)

---

## Why now

The API runs on Render's free plan (512 MB). On 10 Nov 2026 it was down for a long stretch, and a scanned-PDF upload took it down again during the investigation.

Reproduced locally with the production image from `main` and a 512 MB limit:

| State | Memory |
| --- | --- |
| Idle after startup | 55 MB |
| After one scanned-PDF upload (BDRC line + OCR models loaded) | ~580 MB |
| Result at 512 MB | `OOMKilled=true`, exit 137 |
| Same upload with more memory | 200 in ~2 s |

Text spellcheck and digital PDFs never load the models, which is why they kept working. Every scanned-PDF upload kills the instance, Render restarts it, and requests hang or return 502 until it is back. Model weights account for nearly all of the memory, so this predates the November line-fit work (#80). That was not confirmed by rebuilding an older image.

## What production needs

- **Compute:** about 600 MB once OCR has loaded, more for large pages. A three-model vote (see [OCR_ENSEMBLE_AND_DICTIONARY.md](OCR_ENSEMBLE_AND_DICTIONARY.md)) would roughly triple model memory. 2 GB covers both.
- **Database:** only to read the word list. Nothing in `app/` writes to the database in production. `DictionaryService` loads `word.word_normalized` (246k words, 14k distinct syllables) once at startup and never queries again. The corpus is built and edited locally.

## Options (prices as of Nov 2026)

| Option | Approx. cost | Trade-off |
| --- | --- | --- |
| **Render Standard (2 GB), word list shipped in the image** | **$25/mo** | No migration. Always on, so no cold starts. Chosen |
| Render Standard + Render Postgres Basic-1GB | ~$44/mo | Pays for a server to hold read-only data. Worth it once there is user data (accounts, saved jobs) |
| Render Starter | $7/mo | 512 MB, the same as free. Still runs out of memory |
| Fly.io shared CPU, 2 GB | ~$13/mo | Cheaper, per-second billing. Means moving hosts and new deploy config |
| Google Cloud Run, 2 GiB | Likely near $0 at low traffic (bills only while handling requests) | Cheapest. Slow first request after idle while models load, and the most setup |

Sources: Render, Fly.io and Cloud Run pricing pages and third-party summaries, checked 10 Nov 2026. Re-check before committing to a change.

## Decision

Render Standard, without a managed database. It fixes the out-of-memory crashes with the least change. Revisit Cloud Run if the monthly cost starts to matter, and add Postgres when the site stores user data.

## Next steps

1. **Upgrade the instance** to Standard in the Render dashboard, and set `plan: standard` in `render.yaml` in the same change so the two do not disagree. This starts billing.
2. **Ship the word list in the image** (its own PR). Export the syllables or words from the local corpus at build time, or commit a generated file, and have `DictionaryService` read it when no `DATABASE_URL` is set. That turns on dictionary lookup in production for the first time.
   - Golden parity baselines are measured dictionary-off. They stay valid because the parity tests pin the dictionary off. New dictionary-on numbers would be a second set (see [OCR_ENSEMBLE_AND_DICTIONARY.md](OCR_ENSEMBLE_AND_DICTIONARY.md)).
3. **Turn on monitoring** per [MONITORING.md](../guides/MONITORING.md): uptime monitor, Render notifications, Sentry DSNs.
