# API Demo Guide

## Quick Start

Your Tibetan Spell Check API is now live at **http://localhost:8000**

## Interactive Documentation

**Visit**: http://localhost:8000/docs

This gives you a full interactive Swagger UI where you can:

- See all endpoints
- Try them directly in the browser
- View request/response schemas
- See example data

## API Examples

### 1. Check Valid Text

```bash
curl -X POST http://localhost:8000/api/v1/spellcheck/text \
  -H "Content-Type: application/json" \
  -d '{"text": "བོད་ཡིག་གི་སྐད་ཡིག"}'
```

**Response**:

```json
{
  "text": "བོད་ཡིག་གི་སྐད་ཡིག",
  "error_count": 0,
  "errors": []
}
```

### 2. Check Text with Error

```bash
curl -X POST http://localhost:8000/api/v1/spellcheck/text \
  -H "Content-Type: application/json" \
  -d '{"text": "བོད་གཀར་སྐད་ཡིག"}'
```

**Response**:

```json
{
  "text": "བོད་གཀར་སྐད་ཡིག",
  "error_count": 1,
  "errors": [
    {
      "word": "གཀར",
      "position": 4,
      "error_type": "invalid_prefix_combination",
      "severity": "error",
      "message": "Prefix 'ག' cannot prefix root 'ཀ'",
      "component": "prefix"
    }
  ]
}
```

### 3. Check Your Test File Content

```bash
# Extract text from RTF and check via API
TEXT=$(docker compose exec backend python3 -c "
from striprtf.striprtf import rtf_to_text
from pathlib import Path
content = Path('spellchecker_test.rtf').read_text()
print(rtf_to_text(content))
")

curl -X POST http://localhost:8000/api/v1/spellcheck/text \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEXT\"}"
```

## Response Fields

### SpellCheckResponse

| Field         | Type    | Description                        |
| ------------- | ------- | ---------------------------------- |
| `text`        | string  | The original text that was checked |
| `error_count` | integer | Total number of errors found       |
| `errors`      | array   | List of ErrorResponse objects      |

### ErrorResponse

| Field        | Type    | Description                                                           |
| ------------ | ------- | --------------------------------------------------------------------- |
| `word`       | string  | The syllable containing the error                                     |
| `position`   | integer | Character position in original text                                   |
| `error_type` | string  | Type of error (invalid_prefix_combination, invalid_suffix, etc.)      |
| `severity`   | string  | One of: critical, error, info                                         |
| `message`    | string  | Human-readable error description (optional)                           |
| `component`  | string  | Which part failed (prefix, suffix, superscript, subscript) (optional) |

## Error Types

The API can detect:

- `invalid_prefix_combination` - Prefix cannot combine with that root
- `invalid_superscript_combination` - Invalid stacking pattern
- `invalid_suffix` - Not a valid suffix letter
- `invalid_post_suffix` - Not a valid post-suffix
- `missing_root` - Syllable has no root letter
- `encoding_error` - Wrong Unicode character
- `double_vowel` - Two consecutive vowel marks

## Severity Levels

- **critical** 🔴 - Encoding errors, fundamental Unicode issues
- **error** 🟡 - Invalid Tibetan grammar
- **info** 🔵 - Potential issues, informational

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Response**:

```json
{
  "status": "healthy",
  "service": "tibetan-spellchecker"
}
```

## Using from Frontend

```javascript
// Fetch API
const response = await fetch('http://localhost:8000/api/v1/spellcheck/text', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'བོད་ཡིག'}),
})

const data = await response.json()
console.log(`Found ${data.error_count} errors`)
```

```typescript
// With TypeScript types
interface SpellCheckResponse {
  text: string
  error_count: number
  errors: Array<{
    word: string
    position: number
    error_type: string
    severity: 'critical' | 'error' | 'info'
    message?: string
    component?: string
  }>
}
```

## CORS Configuration

The API allows requests from:

- `http://localhost:3000` (Next.js frontend)

To add more origins, edit `backend/app/main.py`:

```python
allow_origins=["http://localhost:3000", "https://your-domain.com"]
```

## API Documentation

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc  
**OpenAPI Schema**: http://localhost:8000/openapi.json

## Test Coverage

```
============================= 113 passed in 0.11s =======================
```

**API Endpoints**: 13 tests

- Valid text: ✅
- Error detection: ✅
- Request validation: ✅
- Edge cases: ✅
- Documentation: ✅

## Demo for Interview

**Show the interviewer**:

1. Live API at http://localhost:8000/docs
2. Click "Try it out" on `/spellcheck/text`
3. Paste Tibetan text
4. Execute and see results
5. Show the structured error response
6. Highlight test coverage (113 tests)

**Talking points**:

- RESTful API design
- Pydantic validation
- OpenAPI/Swagger docs
- Async/await with FastAPI
- Comprehensive test coverage
- Error handling and logging

## Next Steps

**Option 1**: Build frontend UI to consume this API  
**Option 2**: Add PDF upload/download endpoints  
**Option 3**: Add job management for background processing

**Your backend is interview-ready!** 🎉
