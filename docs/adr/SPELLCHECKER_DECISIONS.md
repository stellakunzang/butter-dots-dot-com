# Spellchecker decisions

Each entry is context, the decision, and the consequence. The option lists
that used to live here are in git history.

## ADR-001: Python and FastAPI

**Context.** The spellchecker needed PDF handling and a rule engine. The
frontend was already TypeScript.

**Decision.** Python with FastAPI.

**Consequences.** Two languages in one repo. OCR and PDF libraries are the
reason. The API documents itself through OpenAPI.

## ADR-002: REST

**Context.** The operations are upload, status, and download.

**Decision.** REST, not GraphQL.

**Consequences.** File upload uses ordinary HTTP status codes. There is no
subscription channel. The browser polls job status.

## ADR-003: PostgreSQL

**Context.** The dictionary is relational data. SQLite and MongoDB were the
other candidates.

**Decision.** PostgreSQL.

**Consequences.** A database service in local Docker and in production. The
spellchecker still runs when `DATABASE_URL` is unset. Dictionary lookup is
simply off.

## ADR-004: Background work

**Context.** The early note compared Celery, FastAPI background tasks, and a
hand-rolled worker. It was left open.

**Decision.** In-process FastAPI background tasks. PDFs of 15 pages or fewer
are spellchecked in the request. Larger PDFs are queued and the client polls.

**Consequences.** No Redis and no second worker. A restart drops a queued job.
The "results by email" path logs the notice. No mail provider is configured.

## ADR-005: OCR engine

**Context.** The early note compared Tesseract, Google Cloud Vision, and
EasyOCR, and recorded that Tibetan OCR had been poor.

**Decision.** Scanned pages and broken-font PDFs use the vendored BDRC ONNX
engine. Not Tesseract, and not a cloud vision API.

**Consequences.** Model files are downloaded, not committed. OCR quality is
the limiter on scanned and Himalaya PDFs. See ADR-015 and
`docs/planning/OCR_PARITY_BASELINE.md`.

## ADR-006: Upload size

**Context.** A browser request cannot hold a long book, and an unbounded
upload can stall the process.

**Decision.** 50 MB on the public spellcheck upload. At most 500 pages. Text
spellcheck is capped at 100,000 characters.

**Consequences.** Oversized uploads get HTTP 413. The 15-page sync line is
ADR-004.

## ADR-007: One repository

**Context.** The note left monorepo versus split repos undecided.

**Decision.** One repository: `frontend/`, `backend/`, `database/`, `docs/`.

**Consequences.** Frontend and backend deploy separately. They share this
repo and this changelog.

## ADR-008: Normalized dictionary tables

**Context.** Word lists could have been stored as JSONB documents.

**Decision.** Normalized tables, with indexes, rather than a JSON document
per word.

**Consequences.** Migrations have to change the tables on purpose.
`002_lexicon_schema.sql` is not yet a safe cutover. It drops
`spelling_reference` and uses an untargeted `ON CONFLICT DO NOTHING`.

## ADR-009: Transliteration

**Context.** Wylie spells the written form. Amdo pronunciation does not match
it. The note chose "several systems, clearly labeled."

**Decision.** The spellchecker checks Unicode Tibetan. It does not take Wylie
or phonetic input. The Learn pages explain typing and the written language.
A multi-system transliteration widget was not built.

**Consequences.** Learners meet Wylie in the typing guide, not as a
spellcheck mode.

## ADR-010: Syllables, not code points

**Context.** A Tibetan stack is several code points. NFC and NFD of the same
syllable compare unequal. `len()` is not a character count.

**Decision.** Normalize to NFC, then split on the tsheg (་) and check
syllables.

**Consequences.** Rules and the corpus key on syllables. A raw code-point
scan would disagree with itself.

## ADR-011: Sanskrit

**Context.** Sanskrit written in Tibetan script breaks Tibetan syllable
rules on purpose.

**Decision.** Deferred as its own checker. Sanskrit-likely syllables are
recognized so the spellchecker and the OCR scorer can avoid treating them as
ordinary Tibetan typos.

**Consequences.** A Sanskrit stack is not a full structural check. It is also
not silently ignored in every path.

## ADR-012: Community word submissions

**Context.** Readers could submit words the corpus lacks.

**Decision.** Deferred. The corpus is built from source dictionaries, not
from the site.

**Consequences.** An unknown-word warning stays a warning until a dictionary
load includes the word. There is no public "add this word" action.

## ADR-013: Where words come from

**Context.** A spellchecker needs an attested word list, not definitions.
Single sources carry OCR errors and narrow vocabularies.

**Decision.** Cross-check more than one source. The loader knows Monlam,
botok, and a curated Steinert set. THDL and Rangjung Yeshe were in the early
list. They are not what `build_corpus.py` loads.

**Consequences.** Loading is a manual ops step. It does not run on deploy.
A word in one noisy source does not automatically become attested.

## ADR-014: Structural validation

**Context.** QA input `ཨེརྡ་ཕ༹ཀལ་ཨེཨོརོ་` is three impossible syllables.
The checker flagged one. The parser returned success while leaving stacks
unparsed, and the tests still passed.

**Decision.** Reject syllables with unparsed characters, impossible mark
positions, multiple vowels, a missing root, and similar structural failures.
Report the specific failure, not a generic "invalid."

**Consequences.** The parser and the validator are both on the path. A green
unit test that only checks a happy syllable will miss this class of bug.
`docs/adr/TESTING_PHILOSOPHY.md` is the testing side of the same lesson.

## ADR-015: Broken font encoding

**Context.** Microsoft Himalaya PDFs carry a ToUnicode CMap that does not
round-trip. Copying text out inserts phantom subjoined consonants, and the
codepoints are still Tibetan, so a "not Tibetan Unicode" check does not
fire. PyMuPDF produced the same garbage. A hand-built Himalaya glyph table
would cover one font and break on the next Word export.

**Decision.** If the PDF uses Microsoft Himalaya, render the pages and run
BDRC OCR. A phantom-sequence check remains as a backstop for the vowel-o
corruption.

**Consequences.** Those PDFs are slower than a digital extract, and the OCR
text is not the same as the known text. The Tashi Gyedpa parity fixture
measures that gap. Do not "fix" it by raising the tolerance. See
`docs/planning/OCR_PARITY_BASELINE.md`.
