# Word corpus source dumps

Large dictionary dumps live here for `scripts/build_corpus.py`. They are **gitignored**.

## Obtain sources

### Monlam lexicon (Apache-2.0)

```bash
curl -sL \
  "https://raw.githubusercontent.com/MonlamIT/Tibetan-Lexicon/master/monlam-lexicon-1.txt" \
  -o monlam-lexicon-1.txt
curl -sL \
  "https://raw.githubusercontent.com/MonlamIT/Tibetan-Lexicon/master/LICENSE.txt" \
  -o MONLAM_LICENSE.txt
```

Use `monlam-lexicon-2.txt` (~367k) the same way if you want the larger Grand Dictionary list.

### Botok word list

Copy from the sibling translator app (or any botok JSON export):

```bash
cp ../../tibetan-translator/public/botok-dictionary.json ./botok-dictionary.json
```

### Steinert public dictionaries (Wylie)

Already synced under the sibling translator tree:

`../tibetan-translator/build/dictionaries/`

(from [christiansteinert/tibetan-dictionary](https://github.com/christiansteinert/tibetan-dictionary) `_input/dictionaries/public`). Point `--steinert-dir` at that folder.

## Build

From `backend/` with `DATABASE_URL` set and venv active:

```bash
python scripts/build_corpus.py --sources monlam botok steinert --threshold 1 --dry-run
python scripts/build_corpus.py --sources monlam botok steinert --threshold 1 --replace
```

Restart the backend after loading so `DictionaryService` reloads.

## How this feeds OCR quality + HITL

- Spellcheck emits `unknown_word` warnings for syllables missing from the inventory.
- OCR quality scorer weights that ratio via `W_PHASE2_UNKNOWN` (`app/ocr_assist/quality.py`).
- Each OCR attempt persists errors as `attempts/NN/spellcheck.json` for `/ocr-assist` highlighting.

Tunables, caveats (syllable-level inventory), and when to retune:
[docs/planning/INTERACTIVE_OCR_PLAN.md](../../docs/planning/INTERACTIVE_OCR_PLAN.md) § Living decisions.
