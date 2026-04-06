"""
Tibetan word corpus builder.

Extracts Tibetan words from multiple dictionary sources, cross-references them
(keeping only words that appear in 2+ sources for quality assurance), and loads
the result into the spelling_reference table.

See docs/planning/WORD_CORPUS_PLAN.md for the sourcing strategy.

Usage:
    # From backend/ directory with venv active:
    python scripts/build_corpus.py --help
    python scripts/build_corpus.py --dry-run           # preview counts, no DB write
    python scripts/build_corpus.py --sources thdl ry   # specific sources only
    python scripts/build_corpus.py                     # all available sources → DB

Sources status:
    thdl            — THDL (Tibetan & Himalayan Digital Library)
                      TODO: Download dictionary from https://www.thlib.org
                      Expected format: XML or plain text
                      License: open educational use (verify before redistribution)

    rangjung_yeshe  — Rangjung Yeshe Wiki (Buddhist terminology)
                      TODO: Export via MediaWiki API at https://rywiki.tsadra.org
                      Expected format: MediaWiki XML export or API JSON
                      License: check Creative Commons specifics

    monlam          — Monlam Grand Tibetan Dictionary (~100k entries)
                      TODO: Contact Monlam IT for research/educational access
                      URL: https://www.monlam.ai
                      Status: permission required before use
"""
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

# Minimum number of sources a word must appear in to be included.
CROSS_REFERENCE_THRESHOLD = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def is_tibetan(text: str) -> bool:
    """Return True if text contains at least one Tibetan Unicode character."""
    return any(TIBETAN_RANGE[0] <= ord(c) <= TIBETAN_RANGE[1] for c in text)


# ---------------------------------------------------------------------------
# Source extractors
# ---------------------------------------------------------------------------

def extract_thdl(data_path: Path) -> Iterator[str]:
    """
    Extract Tibetan headwords from a THDL dictionary file.

    TODO: Implement once the THDL dataset has been downloaded.
          Expected: XML or tab-separated text with Tibetan headwords.

    Args:
        data_path: Path to the downloaded THDL dictionary file.

    Yields:
        Tibetan word strings (un-normalized; normalization happens downstream).
    """
    if not data_path.exists():
        logger.warning("THDL data file not found: %s — skipping source", data_path)
        return

    raise NotImplementedError(
        "THDL extractor not yet implemented. "
        "Download the dictionary from https://www.thlib.org first, "
        "then implement the parser for its format here."
    )


def extract_rangjung_yeshe(data_path: Path) -> Iterator[str]:
    """
    Extract Tibetan headwords from a Rangjung Yeshe Wiki export.

    TODO: Implement once the wiki export has been obtained.
          Use the MediaWiki API: https://rywiki.tsadra.org/api.php
          or a full XML dump export.

    Args:
        data_path: Path to the downloaded wiki export file.

    Yields:
        Tibetan word strings.
    """
    if not data_path.exists():
        logger.warning("Rangjung Yeshe data file not found: %s — skipping source", data_path)
        return

    raise NotImplementedError(
        "Rangjung Yeshe extractor not yet implemented. "
        "Export the wiki via MediaWiki API first, "
        "then implement the parser here."
    )


def extract_monlam(data_path: Path) -> Iterator[str]:
    """
    Extract Tibetan headwords from the Monlam Grand Tibetan Dictionary.

    TODO: Contact Monlam IT (https://www.monlam.ai) for research access.
          Do not use without explicit permission.

    Args:
        data_path: Path to the Monlam dataset file.

    Yields:
        Tibetan word strings.
    """
    if not data_path.exists():
        logger.warning("Monlam data file not found: %s — skipping source", data_path)
        return

    raise NotImplementedError(
        "Monlam extractor not yet implemented. "
        "Obtain permission and dataset from Monlam IT first."
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

    Args:
        sources: Mapping of source_name → list of (un-normalized) Tibetan words.
        threshold: Minimum number of sources a word must appear in to be kept.

    Returns:
        List of dicts ready for insertion into spelling_reference.
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
            "source_count": data["source_count"],
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
    """
    Insert validated words into spelling_reference.

    Args:
        words: List of word dicts from cross_reference().
        replace: If True, truncate the table before inserting.

    Returns:
        Number of rows inserted.
    """
    # Import here so the script can be imported without a live DB for --dry-run
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from sqlalchemy import text
    from app.database import get_session, db_available

    if not db_available():
        logger.error("No database connection. Set DATABASE_URL and try again.")
        return 0

    inserted = 0
    with get_session() as session:
        if replace:
            session.execute(text("TRUNCATE spelling_reference"))
            logger.info("Truncated spelling_reference")

        for w in words:
            session.execute(
                text("""
                    INSERT INTO spelling_reference
                        (word, word_normalized, source_count, sources, first_seen_in)
                    VALUES
                        (:word, :word_normalized, :source_count, :sources::jsonb,
                         :first_seen_in)
                    ON CONFLICT (word) DO UPDATE SET
                        source_count = EXCLUDED.source_count,
                        sources      = EXCLUDED.sources
                """),
                {**w, "sources": json.dumps(w["sources"])},
            )
            inserted += 1

    logger.info("Inserted/updated %d words in spelling_reference", inserted)
    return inserted


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SOURCE_MAP = {
    "thdl": ("thdl", extract_thdl, Path("data/thdl_dictionary.txt")),
    "ry": ("rangjung_yeshe", extract_rangjung_yeshe, Path("data/rangjung_yeshe_export.xml")),
    "monlam": ("monlam", extract_monlam, Path("data/monlam_export.json")),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Tibetan word corpus")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SOURCE_MAP.keys()),
        default=list(SOURCE_MAP.keys()),
        help="Which sources to include (default: all)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=CROSS_REFERENCE_THRESHOLD,
        help=f"Minimum sources required per word (default: {CROSS_REFERENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts but do not write to the database",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Truncate spelling_reference before inserting (full rebuild)",
    )
    args = parser.parse_args()

    collected: dict[str, list[str]] = {}
    for key in args.sources:
        source_name, extractor_fn, data_path = SOURCE_MAP[key]
        try:
            words = list(extractor_fn(data_path))
            collected[source_name] = words
            logger.info("Source '%s': %d words", source_name, len(words))
        except NotImplementedError as e:
            logger.warning("Skipping source '%s': %s", key, e)
        except Exception:
            logger.exception("Error reading source '%s'", key)

    if not collected:
        logger.error("No sources produced any words. Exiting.")
        sys.exit(1)

    validated = cross_reference(collected, threshold=args.threshold)

    if args.dry_run:
        logger.info("Dry run — %d words would be written to spelling_reference", len(validated))
        return

    load_to_database(validated, replace=args.replace)


if __name__ == "__main__":
    main()
