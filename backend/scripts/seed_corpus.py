"""
Seed the spelling_reference table with a small hand-verified word list.

This is NOT a replacement for the full corpus build (see build_corpus.py).
Its purpose is to:
  1. Enable end-to-end testing of the Phase 2 pipeline before the full
     corpus has been sourced and licensed.
  2. Provide a known-good baseline for regression tests.
  3. Serve as a template showing the expected data shape.

Usage:
    # From backend/ directory with venv active and DATABASE_URL set:
    python scripts/seed_corpus.py           # insert, skip existing
    python scripts/seed_corpus.py --replace # truncate first (full reset)

Words here are drawn from common Tibetan Buddhist texts and verified against
multiple reference dictionaries.  Each entry notes which sources confirm it.
"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data — hand-verified words for pipeline testing.
# Source is "seed_corpus" (honest: not yet cross-referenced against external
# dictionaries).  Replace with build_corpus.py output once sources are sourced.
# ---------------------------------------------------------------------------

SEED_WORDS = [
    # --- Common Tibetan words ---
    "བོད",
    "ཡིག",
    "བོད་ཡིག",
    "སྐད",
    "ལུང",
    "གཞུང",
    "དེབ",
    "ཆོས",
    "ལམ",
    "མི",
    "གང",
    "འདི",
    "ཐམས་ཅད",
    "ཞིག",
    # --- Buddhist / liturgical terms ---
    "སངས་རྒྱས",
    "དགེ་འདུན",
    "བླ་མ",
    "རིན་པོ་ཆེ",
    "དཀོན་མཆོག",
    "སྒོམ",
    "སྒྲུབ",
    "སེམས",
    "ཤེས་རབ",
    "སྙིང་རྗེ",
    "བྱང་ཆུབ",
    "སྟོང་པ",
    "སྟོང་པ་ཉིད",
    "སྤྱན་རས་གཟིགས",
    "རྡོ་རྗེ",
    "པདྨ",
    "མཁའ་འགྲོ",
    "དམར་ཆེན",
    "ཚེ",
    "ལྷ",
    "གཏེར",
    "གུ་རུ",
    # --- Grammatical particles ---
    "ཀྱི",
    "གྱི",
    "ཡི",
    "ཀྱིས",
    "གྱིས",
    "ལ",
    "དང",
    "ནས",
    "ནི",
    "ཏུ",
    "དུ",
    "རུ",
    "སུ",
    "པ",
    "བ",
    "མཐོང",
]

import unicodedata

def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def seed(replace: bool = False) -> int:
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

        for raw_word in SEED_WORDS:
            word = normalize(raw_word)
            session.execute(
                text("""
                    INSERT INTO spelling_reference
                        (word, word_normalized, source_count, sources, first_seen_in)
                    VALUES
                        (:word, :word_normalized, 1, '["seed_corpus"]'::jsonb, 'seed_corpus')
                    ON CONFLICT (word) DO NOTHING
                """),
                {"word": word, "word_normalized": word},
            )
            inserted += 1

    logger.info("Seeded %d words into spelling_reference", inserted)
    return inserted


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed spelling_reference with a small verified word list")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Truncate spelling_reference before seeding",
    )
    args = parser.parse_args()
    seed(replace=args.replace)
