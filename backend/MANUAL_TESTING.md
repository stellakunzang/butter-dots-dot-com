# Manual Spell Checker Testing Guide

## Quick Start

You can now manually test the spell checker with any Tibetan text file!

**Supported formats**: `.txt`, `.rtf` (Rich Text Format)

### Usage

**Inside Docker** (recommended):
```bash
docker compose exec backend python3 check_file.py <your_file.txt>
# or
docker compose exec backend python3 check_file.py <your_file.rtf>
```

**Or directly** (if you have Python installed):
```bash
cd backend
python3 check_file.py <your_file.txt>
```

## Sample Files Provided

### 1. `sample_text.txt` - Valid Tibetan Text (Plain Text)
Clean text with no errors. Great for testing the checker doesn't flag valid text.

```bash
docker compose exec backend python3 check_file.py sample_text.txt
```

**Expected output**: ✅ No errors found!

### 1b. `sample_text.rtf` - Valid Tibetan Text (RTF Format)
Same as above, but in RTF format to test RTF support.

```bash
docker compose exec backend python3 check_file.py sample_text.rtf
```

**Expected output**: ✅ No errors found! (after RTF conversion)

### 2. `test_with_errors.txt` - Text with Intentional Errors
Contains invalid syllables to test error detection.

```bash
docker compose exec backend python3 check_file.py test_with_errors.txt
```

**Expected output**: 🟡 Error detected (གཀར - invalid prefix combination)

## Testing Your Own Files

### Option 1: Copy file into container
```bash
# Copy your file to the backend directory (works with .txt or .rtf)
cp /path/to/your/tibetan_document.rtf backend/

# Run the checker
docker compose exec backend python3 check_file.py tibetan_document.rtf
```

### Option 2: Mount a volume
Add to your `docker-compose.yml` under backend service:
```yaml
volumes:
  - ./backend:/app
  - ./your-texts:/app/texts  # Add this line
```

Then:
```bash
docker compose up -d
docker compose exec backend python3 check_file.py texts/your_file.txt
```

### Option 3: Use stdin (future enhancement)
```bash
echo "བོད་ཡིག" | docker compose exec -T backend python3 check_file.py -
```

## Understanding the Output

### Severity Levels

- 🔴 **CRITICAL**: Encoding errors, fundamental Unicode issues
- 🟡 **ERROR**: Invalid Tibetan grammar (prefix, subscript, suffix violations)
- 🔵 **INFO**: Potential issues, Sanskrit transliterations

### Error Types

- `invalid_prefix_combination` - Prefix cannot combine with that root (e.g., ག + ཀ)
- `invalid_superscript_combination` - Invalid stacking
- `invalid_subscript_combination` - Invalid subscript
- `encoding_error` - Wrong Unicode character
- `double_vowel` - Two consecutive vowel marks
- And more...

### Example Output

```
======================================================================
SPELL CHECK RESULTS
======================================================================
Total errors found: 1

Summary by severity:
  ERROR: 1

Detailed errors:
----------------------------------------------------------------------

1. 🟡 ERROR: invalid_prefix_combination
   Word: གཀར (at position 44)
   Context: ...ད་ཀྱི་སྐད་ཡིག་ཡིན།

[གཀར]་འདི་ནི་མི་ཁྲིམ་ཡིན།...

======================================================================
```

## Creating Test Files

### Plain Text (.txt)
Just create a UTF-8 encoded text file with Tibetan content:

```tibetan
བོད་ཡིག་གི་སྐད་ཡིག་ནི་བོད་ཀྱི་སྐད་ཡིག་ཡིན།
```

### RTF Files (.rtf)
The spell checker automatically extracts text from RTF files! This means:
- ✅ Works with Microsoft Word `.rtf` exports
- ✅ Works with Pages, LibreOffice, Google Docs RTF exports
- ✅ Preserves Tibetan Unicode text
- ✅ Strips formatting (bold, colors, etc.) and checks the raw text

**How to create RTF from Word/Pages:**
1. Write your Tibetan text in Word, Pages, or any word processor
2. Save As → Rich Text Format (.rtf)
3. Run the spell checker on the `.rtf` file!

### Testing Specific Rules

**Invalid Prefix** (ga cannot prefix ka):
```tibetan
གཀར་
```

**Invalid Prefix** (da cannot prefix nga):
```tibetan
དངས་
```

**Double Vowel** (invalid):
```tibetan
བོོད་
```

## Tips for Testing

1. **Start small**: Test with a few sentences first
2. **Known valid text**: Use text from published Tibetan books
3. **Known errors**: Intentionally create invalid syllables to verify detection
4. **Large documents**: The checker can handle full documents - go ahead!
5. **Performance**: The engine is fast - it can check thousands of syllables per second

## Exit Codes

- `0` = No errors found (success)
- `1` = Errors found (or file error)

This makes it scriptable:
```bash
if docker compose exec backend python3 check_file.py my_text.txt; then
    echo "Text is clean!"
else
    echo "Text has errors"
fi
```

## What Gets Checked

Currently validates:
- ✅ Prefix combinations (5 prefixes: ག ད བ མ འ)
- ✅ Suffix validity (10 suffixes)
- ✅ Post-suffix validity (2: ད ས)
- ✅ Basic superscript/subscript combinations
- ✅ Syllable structure
- ✅ Unicode normalization

## Need More?

Want to check specific aspects? The `TibetanSpellChecker` class in `app/spellcheck/engine.py` has methods you can use in Python:

```python
from app.spellcheck.engine import TibetanSpellChecker

checker = TibetanSpellChecker()

# Check single syllable
error = checker.check_syllable("གཀར")
if error:
    print(f"Error: {error['error_type']}")

# Check full text
errors = checker.check_text("བོད་ཡིག་")
print(f"Found {len(errors)} errors")
```

Happy testing! 🎉
