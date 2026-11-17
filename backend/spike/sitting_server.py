"""Throwaway: local server for a live pecha capture sitting (issue #79).

    cd backend && venv/bin/python -m spike.sitting_server [--vote] [--port 8765]

Open http://localhost:8765 in Safari. Instead of the camera you can open a
PDF of a pecha: each page is imaged as OCR Assist would (embedded scan at
native size, else a 300 DPI render) and read through the same review flow.

Each still from ``sitting.html`` is
OCR'd and scored here, and every capture, decision, and camera event is
appended to ``spike/sittings/<started-at>/log.jsonl`` with the still beside
it. ``spike.summarize_sitting`` turns the log into the plan's tables.

The gate's own call (``quality.decide`` with OCR Assist's default thresholds)
is logged next to yours, so the sitting doubles as gate calibration data.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

from app.ocr_assist.quality import OcrDiagnostics, decide, score_page
from app.ocr_assist.runner import DEFAULT_THRESHOLDS, _default_spellcheck_adapter
from app.pdf.ocr import get_engine
from BDRC.line_detection import FRAGMENT_HEIGHT_RATIO
from spike.ensemble import MODELS

HERE = Path(__file__).parent
SITTINGS = HERE / "sittings"
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg"}


class Sitting:
    def __init__(self, model: str, vote: bool):
        self.model = model
        self.vote = vote
        self.dir = SITTINGS / datetime.now().strftime("%Y%m%d-%H%M%S")
        self.dir.mkdir(parents=True)
        self.log_path = self.dir / "log.jsonl"
        self.lock = threading.Lock()  # one OCR at a time; the engine swaps models
        self.spellcheck = _default_spellcheck_adapter()
        self.dictionary_on = dictionary_available()
        self.pdf: PdfSource | None = None
        self.log("sitting_started", model=model, vote=vote, dictionary=self.dictionary_on)

    def open_pdf(self, body: bytes, name: str) -> dict:
        self.pdf = PdfSource(body)
        (self.dir / "source.pdf").write_bytes(body)
        return self.log("pdf_opened", name=name, pages=self.pdf.page_count, bytes=len(body))

    def log(self, event: str, **fields) -> dict:
        record = {"event": event, "server_ms": int(time.time() * 1000), **fields}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def read(self, image: np.ndarray, model: str) -> list[str]:
        return self.read_marking_fragments(image, model)[0]

    def read_marking_fragments(self, image: np.ndarray, model: str) -> tuple[list[str], list[int]]:
        """Line texts, and the indices of those read from a fragment (a speck or vowel tails).

        Same rule that keeps fragments from bounding a neighbour's crop; the page
        pre-marks these lines removed so you only restore the odd real one.
        """
        lines = get_engine().run_on_image(image, page_settings={"model_variant": model})
        median_h = float(np.median([ln.height for ln in lines])) if len(lines) >= 3 else 0.0
        read = [ln for ln in lines if ln.text]
        fragments = [i for i, ln in enumerate(read) if ln.height < FRAGMENT_HEIGHT_RATIO * median_h]
        return [ln.text for ln in read], fragments

    def score(self, lines: list[str]) -> tuple[dict, list[dict]]:
        text = "\n".join(lines)
        errors = self.spellcheck(text)
        diagnostics = OcrDiagnostics(line_count=len(lines))
        quality = score_page(text, errors, diagnostics)
        return {
            "composite": round(quality.composite_score, 3),
            "gate": decide(quality, DEFAULT_THRESHOLDS, ocr_diagnostics=diagnostics),
            "syllables": quality.tibetan_syllable_count,
            "structural_ratio": round(quality.sanskrit_adjusted_error_ratio, 3),
        }, errors

    def _still_path(self, page: int, attempt: int, content_type: str) -> Path:
        """A fresh filename even if the page number was edited back to one already used."""
        stem, ext = f"page-{page:03d}-a{attempt}", EXTENSIONS.get(content_type, ".bin")
        path, n = self.dir / f"{stem}{ext}", 2
        while path.exists():
            path, n = self.dir / f"{stem}-{n}{ext}", n + 1
        return path

    def capture(self, body: bytes, content_type: str, meta: dict) -> dict:
        received = time.perf_counter()
        page, attempt = int(meta.pop("page")), int(meta.pop("attempt"))
        model = meta.pop("model", None) or self.model
        if model not in MODELS:
            return self.log("capture_failed", page=page, attempt=attempt, reason=f"unknown model {model}")
        expected = int(meta.pop("expected_lines", 0) or 0)
        still = self._still_path(page, attempt, content_type)
        still.write_bytes(body)

        image = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return self.log(
                "capture_failed", page=page, attempt=attempt, reason="undecodable image", **meta
            )

        self.lock.acquire()  # waits here if the last page's vote is still running
        queue_ms = (time.perf_counter() - received) * 1000
        try:
            t0 = time.perf_counter()
            lines, fragments = self.read_marking_fragments(image, model)
            ocr_ms = (time.perf_counter() - t0) * 1000
            scores, errors = self.score(lines)
        except BaseException:
            self.lock.release()
            raise

        record = self.log(
            "capture",
            page=page,
            attempt=attempt,
            model=model,
            still=still.name,
            width=image.shape[1],
            height=image.shape[0],
            bytes=len(body),
            queue_ms=round(queue_ms),
            ocr_ms=round(ocr_ms),
            server_ms_total=round((time.perf_counter() - received) * 1000),
            lines=lines,
            line_count=len(lines),
            fragments=fragments,
            expected_lines=expected or None,
            # The gate only scores what was read; this catches pages read in part.
            lines_short=bool(expected) and len(lines) < expected,
            **scores,
            **meta,
        )
        if self.vote:
            # Off the live path: the vote runs while you look at the result.
            threading.Thread(
                target=self._vote, args=(image, lines, model, page, attempt, still.name), daemon=True
            ).start()
        else:
            self.lock.release()
        return {**record, "errors": [e for e in errors if e.get("position", -1) >= 0]}

    def _vote(
        self, image: np.ndarray, lines: list[str], model: str, page: int, attempt: int, still: str
    ):
        from spike.ensemble import vote_line

        try:
            t0 = time.perf_counter()
            reads = {m: (lines if m == model else self.read(image, m)) for m in MODELS}
            n = min(len(v) for v in reads.values())
            voted = [
                vote_line({m: reads[m][i] for m in MODELS}, None, "Modern")[0] for i in range(n)
            ]
            ms = round((time.perf_counter() - t0) * 1000)
            scores, _ = self.score(voted)
            self.log("vote", page=page, attempt=attempt, still=still, lines=voted, ms=ms, **scores)
        except Exception as err:  # a failed vote must not end the sitting
            self.log("vote_failed", page=page, attempt=attempt, error=repr(err))
        finally:
            self.lock.release()

    def warm(self) -> None:
        """Load the models now so the first page's timing is not a cold start."""
        blank = np.full((600, 900, 3), 255, np.uint8)
        models = [self.model]
        if self.vote:
            models = list(MODELS)
        for model in models:
            self.read(blank, model)
        self.read(blank, self.model)  # leave the main model active


class PdfSource:
    """Pages of an uploaded pecha PDF, imaged the way OCR Assist images them."""

    def __init__(self, body: bytes):
        import fitz

        self.body = body
        self.doc = fitz.open(stream=body, filetype="pdf")
        self.page_count = self.doc.page_count
        self.lock = threading.Lock()  # fitz documents are not thread-safe

    def page_png(self, page: int) -> tuple[bytes, str]:
        """PNG of a 1-based page, and whether it is the embedded scan or a 300 DPI render."""
        from pdf2image import convert_from_bytes

        from app.pdf.extractor import _native_scan_image

        with self.lock:
            image = _native_scan_image(self.doc, self.doc[page - 1])
        source = "pdf.native"
        if image is None:
            rendered = convert_from_bytes(self.body, dpi=300, first_page=page, last_page=page)
            image = cv2.cvtColor(np.array(rendered[0]), cv2.COLOR_RGB2BGR)
            source = "pdf.render300"
        ok, png = cv2.imencode(".png", image)
        if not ok:
            raise ValueError(f"could not encode page {page}")
        return png.tobytes(), source


def dictionary_available() -> bool:
    """True when the word corpus answers; without it only structural errors are flagged."""
    from app.spellcheck.dictionary import DictionaryService

    try:
        return DictionaryService().is_valid_syllable("བཀྲ") is not None
    except Exception:
        return False


def make_handler(sitting: Sitting):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:  # keep the terminal quiet
            pass

        def _json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> bytes:
            return self.rfile.read(int(self.headers.get("Content-Length", 0)))

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/status":
                self._json(
                    {"model": sitting.model, "models": MODELS, "dictionary": sitting.dictionary_on}
                )
                return
            if path.startswith("/pdf/page/"):
                self._pdf_page(path.rsplit("/", 1)[-1])
                return
            if urlparse(self.path).path not in ("/", "/sitting.html"):
                self.send_error(404)
                return
            body = (HERE / "sitting.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _pdf_page(self, raw: str) -> None:
            pdf = sitting.pdf
            if pdf is None or not raw.isdigit() or not 1 <= int(raw) <= pdf.page_count:
                self.send_error(404)
                return
            body, source = pdf.page_png(int(raw))
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Page-Source", source)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            url = urlparse(self.path)
            if url.path == "/pdf":
                name = parse_qs(url.query).get("name", [""])[0]
                try:
                    record = sitting.open_pdf(self._body(), name)
                except Exception as err:
                    self._json({"error": f"could not open the PDF: {err}"}, 400)
                    return
                print(f"PDF opened: {name} ({record['pages']} pages)")
                self._json(record)
            elif url.path == "/capture":
                meta = {k: v[0] for k, v in parse_qs(url.query).items()}
                if "page" not in meta or "attempt" not in meta:
                    self._json({"error": "page and attempt are required"}, 400)
                    return
                record = sitting.capture(self._body(), self.headers.get("Content-Type", ""), meta)
                print(
                    f"page {record.get('page')} attempt {record.get('attempt')}: "
                    f"gate={record.get('gate')} composite={record.get('composite')} ocr={record.get('ocr_ms')}ms"
                )
                self._json(record)
            elif url.path == "/spellcheck":
                # Re-check one line after an edit; positions are within that line.
                text = json.loads(self._body() or b"{}").get("text", "")
                errors = sitting.spellcheck(text)
                self._json({"errors": [e for e in errors if e.get("position", -1) >= 0]})
            elif url.path in ("/decision", "/event"):
                fields = json.loads(self._body() or b"{}")
                kind = "decision" if url.path == "/decision" else fields.pop("kind", "camera_event")
                self._json(sitting.log(kind, **fields))
            else:
                self.send_error(404)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default="Woodblock", choices=MODELS)
    parser.add_argument(
        "--vote", action="store_true", help="also read with all three models and vote"
    )
    args = parser.parse_args()

    sitting = Sitting(args.model, args.vote)
    if not sitting.dictionary_on:
        print(
            "Word corpus is OFF: only structural errors will be flagged. "
            "Start it with `docker compose up -d postgres` and restart."
        )
    print("Loading models…")
    sitting.warm()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(sitting))
    print(f"Sitting log: {sitting.log_path}")
    print(f"Open http://127.0.0.1:{args.port} in Safari. Ctrl-C to end the sitting.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sitting.log("sitting_ended")
        print(f"\nSummarize with: venv/bin/python -m spike.summarize_sitting {sitting.dir}")


if __name__ == "__main__":
    main()
