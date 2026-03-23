"""
Download BDRC OCR models from GitHub releases.

The BDRC OCR models are not checked into the repository (too large).
Run this script once before starting the server:

    python3 scripts/download_models.py

Models are saved to backend/OCRModels/ (gitignored).
Line detection models are saved to backend/Models/ (gitignored).

Source: buda-base/tibetan-ocr-app (MIT License)
        https://github.com/buda-base/tibetan-ocr-app
"""
import sys
import zipfile
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent

# OCR models (Uchen, Woodblock, Ume, etc.)
OCR_MODELS_URL = (
    "https://github.com/buda-base/tibetan-ocr-app/releases/download/"
    "v0.1/bdrc_ocr_models_1.0.zip"
)
OCR_MODELS_DIR = BACKEND_DIR / "OCRModels"

# Line detection models
LINE_MODEL_URL = (
    "https://github.com/buda-base/tibetan-ocr-app/releases/download/"
    "v0.1/PhotiLines.onnx"
)
LAYOUT_MODEL_URL = (
    "https://github.com/buda-base/tibetan-ocr-app/releases/download/"
    "v0.1/photi.onnx"
)
MODELS_DIR = BACKEND_DIR / "Models"
LINES_DIR = MODELS_DIR / "Lines"
LAYOUT_DIR = MODELS_DIR / "Layout"


def download_file(url: str, dest: Path, label: str) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  [skip] {label} already downloaded")
        return

    print(f"  Downloading {label}...")
    dest.parent.mkdir(parents=True, exist_ok=True)

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = min(int(count * block_size * 100 / total_size), 100)
            print(f"\r    {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print(f"\r    done ({dest.stat().st_size // 1024 // 1024} MB)")


def download_and_extract_zip(url: str, dest_dir: Path, label: str) -> None:
    zip_path = dest_dir.parent / f"{dest_dir.name}.zip"

    if dest_dir.exists() and any(dest_dir.rglob("*.onnx")):
        print(f"  [skip] {label} already extracted")
        return

    print(f"  Downloading {label}...")
    dest_dir.mkdir(parents=True, exist_ok=True)

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = min(int(count * block_size * 100 / total_size), 100)
            print(f"\r    {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, zip_path, reporthook=progress)
    print(f"\r    downloaded, extracting...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    zip_path.unlink()
    model_count = len(list(dest_dir.rglob("*.onnx")))
    print(f"    extracted {model_count} model files to {dest_dir}")


def main():
    print("BDRC OCR Model Downloader")
    print("=" * 40)
    print(f"Saving to: {BACKEND_DIR}\n")

    print("1. Line detection models")
    download_file(LINE_MODEL_URL, LINES_DIR / "PhotiLines.onnx", "PhotiLines.onnx")
    download_file(LAYOUT_MODEL_URL, LAYOUT_DIR / "photi.onnx", "photi.onnx")

    print("\n2. OCR models (Uchen, Woodblock, Ume, Dunhuang)")
    download_and_extract_zip(OCR_MODELS_URL, OCR_MODELS_DIR, "bdrc_ocr_models_1.0.zip")

    # List available OCR models
    if OCR_MODELS_DIR.exists():
        models = [d.name for d in OCR_MODELS_DIR.iterdir() if d.is_dir()]
        if models:
            print(f"\nAvailable OCR models: {', '.join(models)}")
            print("Set OCR_MODEL_NAME in .env to choose (default: Uchen)")

    print("\nAll models ready.")


if __name__ == "__main__":
    main()
