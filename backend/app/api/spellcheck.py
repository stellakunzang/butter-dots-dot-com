"""
Spell check API endpoints.
"""
from fastapi import APIRouter, HTTPException
from app.schemas.spellcheck import SpellCheckRequest, SpellCheckResponse, ErrorResponse
from app.spellcheck.engine import TibetanSpellChecker


router = APIRouter()


@router.post("/spellcheck/text", response_model=SpellCheckResponse)
async def check_text(request: SpellCheckRequest):
    """
    Check Tibetan text for spelling errors.
    
    Returns a list of errors with their positions, types, and severity levels.
    Uses grammatical rules to validate:
    - Prefix combinations
    - Superscript combinations  
    - Suffix validity
    - Post-suffix validity
    - Syllable structure
    """
    try:
        # Initialize spell checker
        checker = TibetanSpellChecker()
        
        # Run spell check
        raw_errors = checker.check_text(request.text)
        
        # Convert to response format
        errors = [
            ErrorResponse(
                word=error.get('word', ''),
                position=error.get('position', 0),
                error_type=error.get('error_type', 'unknown'),
                severity=error.get('severity', 'error'),
                message=error.get('message'),
                component=error.get('component')
            )
            for error in raw_errors
        ]
        
        return SpellCheckResponse(
            text=request.text,
            error_count=len(errors),
            errors=errors
        )
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing spell check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing spell check: {str(e)}"
        )
