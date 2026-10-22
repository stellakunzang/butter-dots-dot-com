"""The shared OCR engine does not load or swap models from two threads at once."""

import threading
import time

from app.pdf.ocr import BDRCOCREngine


def test_load_runs_once():
    engine = BDRCOCREngine()
    calls = []

    def fake_load():
        calls.append(1)
        engine._ready = True

    engine._load_unlocked = fake_load
    engine._load()
    engine._load()
    assert calls == [1]


def test_model_swap_does_not_overlap():
    engine = BDRCOCREngine()
    engine._ready = True
    engine._active_model_name = "woodblock"
    engine._model_config_cache["ume"] = {"name": "ume"}
    engine._model_config_cache["modern"] = {"name": "modern"}

    state = {"in_flight": 0, "max": 0}

    class Pipeline:
        def update_ocr_model(self, config):
            state["in_flight"] += 1
            state["max"] = max(state["max"], state["in_flight"])
            time.sleep(0.05)
            state["in_flight"] -= 1

    engine._pipeline = Pipeline()
    threads = [
        threading.Thread(target=engine._ensure_ocr_model, args=("ume",)),
        threading.Thread(target=engine._ensure_ocr_model, args=("modern",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert state["max"] == 1
