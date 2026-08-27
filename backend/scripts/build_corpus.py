"""
Tibetan word corpus builder.

Extracts Tibetan words from multiple dictionary sources, optionally
cross-references them, and loads the result into word + word_source.

See docs/planning/WORD_CORPUS_PLAN.md and backend/data/README.md.

Usage (from backend/ with venv active):
    python scripts/build_corpus.py --help
    python scripts/build_corpus.py --sources monlam botok steinert --threshold 1 --dry-run
    python scripts/build_corpus.py --sources monlam botok steinert --threshold 1 --replace

Sources:
    monlam    — MonlamIT/Tibetan-Lexicon (Apache-2.0). UTF-16 .txt with tsek.
    botok     — botok-style JSON {\"words\": [{\"word\": \"...\"}, ...]}.
    steinert  — christiansteinert public dict dumps (Wylie|definition lines);
                converted to Unicode via pyewts. Default dir: sibling
                tibetan-translator/build/dictionaries/.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import unicodedata
from pathlib import Path
from typing import Iterator

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TSHEG = "\u0F0B"  # ་
TIBETAN_RANGE = (0x0F00, 0x0FFF)

# Default for first local builds. Raise to 2+ once sources are trusted.
CROSS_REFERENCE_THRESHOLD = 1

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"

# Curated subset of Steinert public dictionaries (Wylie headwords).
# Full set lives in tibetan-translator/build/dictionaries/; expand later.
STEINERT_PUBLIC_DICTS = (
    "02-RangjungYeshe",
    "07-JimValby",
    "08-IvesWaldo",
    "09-DanMartin",
    "10-RichardBarron",
)

DEFAULT_STEINERT_DIR = (
    BACKEND_ROOT.parent.parent / "tibetan-translator" / "build" / "dictionaries"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def is_tibetan(text: str) -> bool:
    """Return True if text contains at least one Tibetan Unicode character."""
    return any(TIBETAN_RANGE[0] <= ord(c) <= TIBETAN_RANGE[1] for c in text)


def _strip_bom(text: str) -> str:
    return text.lstrip("\ufeff")


# ---------------------------------------------------------------------------
# Source extractors
# ---------------------------------------------------------------------------

def extract_monlam(data_path: Path) -> Iterator[str]:
    """
    Extract headwords from MonlamIT Tibetan-Lexicon UTF-16 text dumps.

    File is UTF-16 (LE) with a header line ``word``. Entries already include
    inter-syllable tsek for multi-syllable forms.
    """
    if not data_path.exists():
        logger.warning("Monlam data file not found: %s — skipping source", data_path)
        return

    raw = data_path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8")

    for line in text.splitlines():
        word = _strip_bom(line).strip()
        if not word or word.lower() == "word":
            continue
        if is_tibetan(word):
            yield word


def extract_botok_json(data_path: Path) -> Iterator[str]:
    """Extract words from a botok-style JSON export."""
    if not data_path.exists():
        logger.warning("Botok JSON not found: %s — skipping source", data_path)
        return

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    entries = payload.get("words", payload if isinstance(payload, list) else [])
    for entry in entries:
        if isinstance(entry, str):
            word = entry
        elif isinstance(entry, dict):
            word = entry.get("word") or entry.get("text") or ""
        else:
            continue
        word = str(word).strip()
        if word and is_tibetan(word):
            yield word


def extract_steinert_dir(data_path: Path) -> Iterator[str]:
    """
    Extract Tibetan headwords from Steinert-format dictionary files.

    Each file is ``wylie headword|definition`` (UTF-8). Headwords are converted
    to Unicode with pyewts. Only the curated PUBLIC list is read unless the
    directory contains fewer matching names (then all non-hidden files).
    """
    if not data_path.exists():
        logger.warning("Steinert dict dir not found: %s — skipping source", data_path)
        return

    try:
        import pyewts
    except ImportError:
        logger.error("pyewts is required for steinert extraction (pip install pyewts)")
        return

    converter = pyewts.pyewts()
    files = [data_path / name for name in STEINERT_PUBLIC_DICTS]
    existing = [p for p in files if p.is_file()]
    if not existing:
        # Fall back to every plain file in the directory.
        existing = sorted(
            p for p in data_path.iterdir() if p.is_file() and not p.name.startswith(".")
        )
        logger.info(
            "Curated Steinert list not found; using %d files in %s",
            len(existing),
            data_path,
        )
    else:
        logger.info("Using %d curated Steinert public dictionaries", len(existing))

    converted = 0
    skipped = 0
    for path in existing:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.exception("Failed to read %s", path)
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            head = line.split("|", 1)[0].strip()
            if not head:
                continue
            try:
                tibetan = converter.toUnicode(head)
            except Exception:
                skipped += 1
                continue
            tibetan = normalize(tibetan)
            if tibetan and is_tibetan(tibetan):
                converted += 1
                yield tibetan
            else:
                skipped += 1

    logger.info(
        "Steinert Wylie→Unicode: %d headwords yielded, %d skipped",
        converted,
        skipped,
    )


# ---------------------------------------------------------------------------
# Cross-referencing
# ---------------------------------------------------------------------------

def cross_reference(
    sources: dict[str, list[str]],
    threshold: int = CROSS_REFERENCE_THRESHOLD,
) -> list[dict]:
    """
    Combine word lists from multiple sources and filter by cross-reference count.
    """
    word_data: dict[str, dict] = {}

    for source_name, words in sources.items():
        seen_in_source: set[str] = set()
        for raw_word in words:
            word = normalize(raw_word)
            if not word or not is_tibetan(word):
                continue
            if word in seen_in_source:
                continue
            seen_in_source.add(word)

            if word not in word_data:
                word_data[word] = {"sources": [], "source_count": 0}
            word_data[word]["sources"].append(source_name)
            word_data[word]["source_count"] += 1

    total = len(word_data)
    validated = [
        {
            "word": word,
            "word_normalized": word,
            "sources": data["sources"],
            "first_seen_in": data["sources"][0],
        }
        for word, data in word_data.items()
        if data["source_count"] >= threshold
    ]

    logger.info(
        "Cross-reference: %d total unique words → %d validated (threshold: %d+ sources)",
        total,
        len(validated),
        threshold,
    )
    return validated


# ---------------------------------------------------------------------------
# Database loader
# ---------------------------------------------------------------------------

def load_to_database(words: list[dict], replace: bool = False) -> int:
    """Insert validated headwords into word and word_source (batched)."""
    sys.path.insert(0, str(BACKEND_ROOT))

    from sqlalchemy import text
    from app.database import get_session, db_available

    if not db_available():
        logger.error("No database connection. Set DATABASE_URL and try again.")
        return 0

    if not words:
        return 0

    all_keys = sorted({k for w in words for k in w["sources"]})
    with get_session() as session:
        if replace:
            session.execute(text("TRUNCATE word RESTART IDENTITY CASCADE"))
            logger.info("Truncated word (CASCADE to word_source, definition)")

        for key in all_keys:
            session.execute(
                text("""
                    INSERT INTO source (source_key, display_name) VALUES (:k, :k)
                    ON CONFLICT (source_key) DO NOTHING
                """),
                {"k": key},
            )

        # Batch headwords — ON CONFLICT skips duplicates within/across runs.
        batch_size = 5000
        for i in range(0, len(words), batch_size):
            chunk = words[i : i + batch_size]
            session.execute(
                text("""
                    INSERT INTO word (word, word_normalized, first_seen_in)
                    VALUES (:word, :word_normalized, :first_seen_in)
                    ON CONFLICT (word) DO NOTHING
                """),
                [
                    {
                        "word": w["word"],
                        "word_normalized": w["word_normalized"],
                        "first_seen_in": w["first_seen_in"],
                    }
                    for w in chunk
                ],
            )
            if (i // batch_size + 1) % 10 == 0 or i + batch_size >= len(words):
                logger.info(
                    "… word rows upserted through %d / %d",
                    min(i + batch_size, len(words)),
                    len(words),
                )

        # Map source_key → id once.
        source_ids = {
            row[0]: row[1]
            for row in session.execute(
                text("SELECT source_key, id FROM source")
            ).fetchall()
        }

        # Resolve word → id for provenance links (only words we care about).
        word_ids: dict[str, int] = {}
        for i in range(0, len(words), batch_size):
            chunk_words = [w["word"] for w in words[i : i + batch_size]]
            rows = session.execute(
                text("SELECT word, id FROM word WHERE word = ANY(:ws)"),
                {"ws": chunk_words},
            ).fetchall()
            for word, wid in rows:
                word_ids[word] = wid

        link_rows = []
        for w in words:
            wid = word_ids.get(w["word"])
            if wid is None:
                continue
            for skey in w["sources"]:
                sid = source_ids.get(skey)
                if sid is not None:
                    link_rows.append({"wid": wid, "sid": sid})

        for i in range(0, len(link_rows), batch_size):
            chunk = link_rows[i : i + batch_size]
            session.execute(
                text("""
                    INSERT INTO word_source (word_id, source_id)
                    VALUES (:wid, :sid)
                    ON CONFLICT (word_id, source_id) DO NOTHING
                """),
                chunk,
            )
            if (i // batch_size + 1) % 10 == 0 or i + batch_size >= len(link_rows):
                logger.info(
                    "… word_source links through %d / %d",
                    min(i + batch_size, len(link_rows)),
                    len(link_rows),
                )

    written = len(words)
    logger.info("Wrote %d headwords to word + word_source", written)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _source_map(steinert_dir: Path) -> dict:
    return {
        "monlam": ("monlam", extract_monlam, DATA_DIR / "monlam-lexicon-1.txt"),
        "botok": ("botok", extract_botok_json, DATA_DIR / "botok-dictionary.json"),
        "steinert": ("steinert", extract_steinert_dir, steinert_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Tibetan word corpus")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["monlam", "botok", "steinert"],
        default=["monlam", "botok", "steinert"],
        help="Which sources to include (default: monlam botok steinert)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=CROSS_REFERENCE_THRESHOLD,
        help=f"Minimum sources required per word (default: {CROSS_REFERENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--steinert-dir",
        type=Path,
        default=DEFAULT_STEINERT_DIR,
        help="Directory of Steinert Wylie dictionary files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts but do not write to the database",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Truncate word (and word_source) before inserting (full rebuild)",
    )
    args = parser.parse_args()

    source_map = _source_map(args.steinert_dir.resolve())
    collected: dict[str, list[str]] = {}
    for key in args.sources:
        source_name, extractor_fn, data_path = source_map[key]
        try:
            words = list(extractor_fn(data_path))
            if words:
                collected[source_name] = words
                logger.info("Source '%s': %d words", source_name, len(words))
            else:
                logger.warning("Source '%s' produced 0 words", source_name)
        except Exception:
            logger.exception("Error reading source '%s'", key)

    if not collected:
        logger.error("No sources produced any words. See backend/data/README.md")
        sys.exit(1)

    validated = cross_reference(collected, threshold=args.threshold)

    if args.dry_run:
        logger.info(
            "Dry run — %d words would be written to word + word_source",
            len(validated),
        )
        return

    load_to_database(validated, replace=args.replace)


if __name__ == "__main__":
    main()
