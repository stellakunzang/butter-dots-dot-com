"""Throwaway: turn a sitting log into the tables LIVE_PECHA_CAPTURE.md asks for (issue #79).

    cd backend && venv/bin/python -m spike.summarize_sitting spike/sittings/<started-at>

Prints Markdown and writes it to ``summary.md`` beside the log.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

PAGES_IN_A_BOOK = 200


def load(log_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def _row(name: str, values: list[float], unit: str = "s", scale: float = 1000) -> str:
    if not values:
        return f"| {name} | — | — | — |"
    v = [x / scale for x in values]
    return f"| {name} | {statistics.median(v):.1f} {unit} | {_pct(v, 0.9):.1f} {unit} | {len(v)} |"


def _versus(title: str, decisions: list[dict], gate_of, gates: list[str]) -> list[str]:
    counts = Counter((gate_of(d), d["decision"]) for d in decisions)
    choices = ["accept", "retake", "flag"]
    out = [
        "",
        f"### {title}",
        "",
        "| Gate ↓ / you → | " + " | ".join(choices) + " |",
        "| --- |" + " --- |" * len(choices),
    ]
    for g in gates:
        out.append(f"| {g} | " + " | ".join(str(counts[(g, c)]) for c in choices) + " |")
    return out


def summarize(records: list[dict]) -> str:
    captures = [r for r in records if r["event"] == "capture"]
    decisions = [r for r in records if r["event"] == "decision"]
    camera = [r for r in records if r["event"] == "camera_event"]
    votes = [r for r in records if r["event"] == "vote"]
    by_attempt = {(c["page"], c["attempt"]): c for c in captures}

    done = [d for d in decisions if d["decision"] in ("accept", "flag")]
    retakes = [d for d in decisions if d["decision"] == "retake"]
    pages = sorted({d["page"] for d in done})
    attempts_per_page = Counter(d["page"] for d in decisions)

    cycle = [b["client_decision_ms"] - a["client_decision_ms"] for a, b in zip(done, done[1:])]
    round_trip = [
        d["client_result_ms"] - d["client_capture_ms"] for d in decisions if "client_result_ms" in d
    ]
    review = [
        d["client_decision_ms"] - d["client_result_ms"]
        for d in decisions
        if "client_result_ms" in d
    ]
    ocr = [c["ocr_ms"] for c in captures]
    vote = [v["ms"] for v in votes] + [c["vote"]["ms"] for c in captures if "vote" in c]
    queue = [c["queue_ms"] for c in captures if c.get("queue_ms", 0) > 100]

    out = ["## Sitting summary", ""]
    started = records[0]
    out.append(f"Model: {started.get('model')}; vote: {started.get('vote')}.")
    if len(records) > 1:
        minutes = (records[-1]["server_ms"] - started["server_ms"]) / 60000
        out.append(f"Wall clock: {minutes:.1f} min.")
    out += [
        "",
        "| Pages done | Accepted | Flagged | Retakes | Retake rate | Pages needing >1 attempt |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| {len(pages)} | {sum(d['decision'] == 'accept' for d in done)} | "
        f"{sum(d['decision'] == 'flag' for d in done)} | {len(retakes)} | "
        f"{(len(retakes) / len(pages) if pages else 0):.0%} | "
        f"{sum(1 for p in pages if attempts_per_page[p] > 1)} |",
        "",
        "### Latency",
        "",
        "| Step | Median | p90 | n |",
        "| --- | --- | --- | --- |",
        _row("OCR (server)", ocr),
        _row("Capture → result shown", round_trip),
        _row("Result → your decision", review),
        _row("Page to page (decision to decision, incl. turning and framing)", cycle),
    ]
    if vote:
        out.insert(-1, _row("Three-model vote", vote))
    if queue:
        out.insert(-1, _row("Capture waited on the last vote", queue))
    if cycle:
        med, p90 = statistics.median(cycle) / 60000, _pct(cycle, 0.9) / 60000
        out += [
            "",
            f"Projected {PAGES_IN_A_BOOK}-page book: {med * PAGES_IN_A_BOOK:.0f} min at the median pace, "
            f"{p90 * PAGES_IN_A_BOOK:.0f} min at the p90 pace.",
        ]

    def gate_of(d: dict) -> str:
        return by_attempt.get((d["page"], d["attempt"]), {}).get("gate", "?")

    def gate_with_lines(d: dict) -> str:
        c = by_attempt.get((d["page"], d["attempt"]), {})
        return "lines short" if c.get("lines_short") else c.get("gate", "?")

    out += _versus("Gate vs you", decisions, gate_of, ["accept", "escalate", "reject"])
    if any(c.get("expected_lines") for c in captures):
        out += _versus(
            "Gate plus line check vs you",
            decisions,
            gate_with_lines,
            ["accept", "escalate", "reject", "lines short"],
        )

    if vote:
        voted = {(v["page"], v["attempt"]): v for v in votes}
        pairs = [(c["composite"], c["vote"]["composite"]) for c in captures if "vote" in c] + [
            (c["composite"], voted[(c["page"], c["attempt"])]["composite"])
            for c in captures
            if (c["page"], c["attempt"]) in voted
        ]
        better = sum(v > s for s, v in pairs)
        out += [
            "",
            f"Vote composite higher than single model on {better} of {len(pairs)} captures.",
        ]

    saved = [d for d in done if "marks_left" in d]
    if saved:
        fixed = [d for d in saved if d.get("final_lines")]
        out += [
            "",
            "### Fixes during capture",
            "",
            f"{len(fixed)} of {len(saved)} saved leaves were fixed before saving "
            f"({sum(len(d.get('edits', [])) for d in fixed)} lines edited, "
            f"{sum(len(d.get('removed', [])) for d in fixed)} removed). "
            f"Marks left for later: {sum(d['marks_left'] for d in saved)}.",
        ]

    judged = [d for d in done if "premarked" in d]
    if judged:
        premarked = sum(len(d["premarked"]) for d in judged)
        restored = sum(len(d["restored"]) for d in judged)
        missed = sum(len(d["removed_by_you"]) for d in judged)
        out += [
            "",
            "### Pre-marked stray lines",
            "",
            f"{premarked} lines pre-marked across {len(judged)} saved leaves; you restored {restored} "
            f"as real text and removed {missed} more yourself.",
        ]

    if camera:
        out += ["", "### Camera events and notes", "", "| Event | Count |", "| --- | --- |"]
        for kind, n in Counter(e.get("type") for e in camera).most_common():
            out.append(f"| {kind} | {n} |")
        notes = [e for e in camera if e.get("type") == "note"] + [
            d for d in decisions if d.get("note")
        ]
        if notes:
            out += ["", "Notes:"] + [f"- page {n.get('page', '?')}: {n['note']}" for n in notes]
    return "\n".join(out) + "\n"


def transcript(records: list[dict]) -> str:
    """Final text per saved leaf: your fixes if any, else the OCR reading. Last save wins."""
    captures = {(r["page"], r["attempt"]): r for r in records if r["event"] == "capture"}
    pages: dict[int, tuple[dict, list[str]]] = {}
    for d in records:
        if d["event"] == "decision" and d["decision"] in ("accept", "flag"):
            lines = d.get("final_lines") or captures.get((d["page"], d["attempt"]), {}).get("lines", [])
            pages[d["page"]] = (d, lines)
    out = []
    for page in sorted(pages):
        d, lines = pages[page]
        tags = ["flagged for proofing"] if d["decision"] == "flag" else []
        if d.get("marks_left"):
            tags.append(f"{d['marks_left']} marked syllables")
        out += [f"--- leaf {page}" + (f" ({', '.join(tags)})" if tags else "") + " ---", *lines, ""]
    return "\n".join(out)


def main() -> None:
    sitting = Path(sys.argv[1])
    log_path = sitting / "log.jsonl" if sitting.is_dir() else sitting
    summary = summarize(load(log_path))
    (log_path.parent / "summary.md").write_text(summary, encoding="utf-8")
    (log_path.parent / "transcript.txt").write_text(transcript(load(log_path)), encoding="utf-8")
    print(summary)
    print(f"Transcript: {log_path.parent / 'transcript.txt'}")


if __name__ == "__main__":
    main()
