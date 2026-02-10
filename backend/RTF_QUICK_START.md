# RTF Support - Quick Start

## ✅ RTF Files Now Supported!

The spell checker can now read **Rich Text Format (.rtf)** files directly!

## Usage

```bash
docker compose exec backend python3 check_file.py your_document.rtf
```

## What This Means

✅ **Export from Word, Pages, or any word processor as RTF**  
✅ **Keep your formatting while writing**  
✅ **Run spell checker on the exported file**  
✅ **All Tibetan Unicode preserved**  

## Quick Test

**Test with valid RTF:**
```bash
docker compose exec backend python3 check_file.py sample_text.rtf
```

**Test with errors in RTF:**
```bash
docker compose exec backend python3 check_file.py test_with_errors.rtf
```

## How It Works

1. Script reads the `.rtf` file
2. Extracts plain text (strips formatting)
3. Runs spell checker on the text
4. Reports errors with positions in the plain text

## Export as RTF from Your Editor

**Microsoft Word:**
- File → Save As → Format: Rich Text Format (.rtf)

**Pages (Mac):**
- File → Export To → RTF

**Google Docs:**
- File → Download → Rich Text Format (.rtf)

**LibreOffice:**
- File → Save As → File type: Rich Text Format (.rtf)

## Supported Formats

- ✅ `.txt` - Plain text files (UTF-8)
- ✅ `.rtf` - Rich Text Format

## What Gets Checked

The spell checker validates:
- Prefix combinations (ག ད བ མ འ)
- Suffix validity (10 valid suffixes)
- Post-suffix validity (ད ས)
- Superscript/subscript stacking
- Syllable structure
- Unicode normalization

Same validation as with `.txt` files!

## Notes

- **RTF formatting is stripped** - Only the text content is checked
- **Position numbers** refer to the plain text after RTF conversion
- **All Tibetan Unicode characters are preserved** during conversion
- Works with **any RTF file** regardless of which program created it

## Next Steps

Want to use this with actual documents? Just:
1. Write/edit your Tibetan text in your favorite word processor
2. Export as RTF
3. Copy to `backend/` directory
4. Run: `docker compose exec backend python3 check_file.py your_file.rtf`

Happy checking! 📝✨
