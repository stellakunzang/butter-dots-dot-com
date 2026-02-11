# Test Suite Documentation

## Overview

Tests are organized to mirror the spellcheck pipeline architecture:

```
char_typing -> parsing -> validation
      \          |          /
       \         |         /
        rules/stacking (data)
```

## Test Files

### Pipeline Stage Tests

| Test File | Tests For | Source Module |
|---|---|---|
| `test_stacking_rules.py` | Stacking rule data and lookups | `rules/stacking.py` |
| `test_splitting.py` | Syllable splitting by tsheg | `splitter.py` |
| `test_parsing.py` | Syllable parsing (root, prefix, superscript, subscripts, vowels, suffixes) | `parsing/parser.py` |
| `test_validation.py` | Pattern checks, completeness checks, component validation, impossible structures | `validation/` |
| `test_normalizer.py` | Unicode normalization | `normalizer.py` |

### Integration Tests

| Test File | Tests For |
|---|---|
| `test_engine.py` | Full spellcheck engine pipeline (end-to-end) |
| `test_real_tibetan_words.py` | Real-world Unicode encoding and word structure |

### API Tests

| Test File | Tests For |
|---|---|
| `test_api_spellcheck.py` | Spellcheck REST API endpoint |
| `test_health.py` | Health check endpoint |

### Support Files

| File | Purpose |
|---|---|
| `test_helpers.py` | Shared test utilities (`get_root_base_form`, `assert_components`) |
| `conftest.py` | Pytest fixtures |

## Critical Tests

`test_parsing.py::TestRegressionBugs` contains regression tests for parser bugs discovered 2026-02-11. **DO NOT REMOVE** these tests:

1. `test_regression_skad_superscript` - སྐད superscript was misidentified as root
2. `test_regression_brgyud_root` - བརྒྱུད subscript was misidentified as root
3. `test_regression_spyod_structure` - སྤྱོད all components must parse correctly

## Running Tests

```bash
# All tests (with pytest)
python3 -m pytest backend/tests/ -v

# Specific pipeline stage
python3 -m pytest backend/tests/test_parsing.py -v
python3 -m pytest backend/tests/test_validation.py -v
python3 -m pytest backend/tests/test_stacking_rules.py -v

# Specific test class
python3 -m pytest backend/tests/test_parsing.py::TestRegressionBugs -v

# Without pytest (manual)
cd backend
python3 -c "
from tests.test_parsing import TestRegressionBugs
t = TestRegressionBugs()
t.test_regression_skad_superscript()
t.test_regression_brgyud_root()
print('Regression tests passed')
"
```

## Test Naming Convention

```python
def test_<feature>_<scenario>():
    """<Clear description>"""

def test_regression_<bug_name>():
    """REGRESSION: <Description of bug that was fixed>"""
```

## When Adding Tests

- **Parser changes** -> add to `test_parsing.py`
- **New stacking rules** -> add to `test_stacking_rules.py`
- **New validation checks** -> add to `test_validation.py`
- **Splitting changes** -> add to `test_splitting.py`
- **Bug fix** -> add regression test with `REGRESSION:` docstring prefix
