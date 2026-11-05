"""Throwaway: run Continuity Camera stills through every BDRC model (issue #79, § 0).

    cd backend && venv/bin/python -m spike.leaf_readability spike/stills/leaf-*.jpg
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from app.ocr_assist.quality import OcrDiagnostics, score_page
from app.ocr_assist.runner import _default_ocr_adapter, _default_spellcheck_adapter
from app.pdf.ocr import OCR_MODELS_DIR

OUT_DIR = Path(__file__).parent / "out"


def main(paths: list[str]) -> None:
    ocr = _default_ocr_adapter()
    spellcheck = _default_spellcheck_adapter()
    models = sorted(p.name for p in OCR_MODELS_DIR.iterdir() if p.is_dir())
    OUT_DIR.mkdir(exist_ok=True)

    print(f"{'still':<12} {'model':<17} {'lines':>5} {'syl':>5} {'struct':>7} "
          f"{'unknown':>7} {'comp':>5} {'secs':>5}")
    for raw in paths:
        image = Path(raw)
        for model in models:
            start = time.perf_counter()
            result = ocr(image, {"model_variant": model})
            errors = spellcheck(result.text)
            quality = score_page(result.text, errors, OcrDiagnostics(line_count=result.line_count))
            elapsed = time.perf_counter() - start

            (OUT_DIR / f"{image.stem}.{model}.txt").write_text(result.text, encoding="utf-8")
            print(
                f"{image.stem:<12} {model:<17} {result.line_count:>5} "
                f"{quality.tibetan_syllable_count:>5} "
                f"{quality.sanskrit_adjusted_error_ratio:>7.3f} "
                f"{quality.unknown_word_ratio:>7.3f} "
                f"{quality.composite_score:>5.2f} {elapsed:>5.1f}"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
