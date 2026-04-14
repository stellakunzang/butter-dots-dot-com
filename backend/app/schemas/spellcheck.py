"""
Pydantic schemas for spell check API requests and responses.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SpellCheckRequest(BaseModel):
    """Request to check Tibetan text for spelling errors."""
    
    text: str = Field(
        ...,
        description="Tibetan text to check for spelling errors",
        min_length=1,
        max_length=100_000,
        examples=["བོད་ཡིག་གི་སྐད་ཡིག"]
    )


class ErrorResponse(BaseModel):
    """Individual spelling error in the text."""
    
    word: str = Field(
        ...,
        description="The syllable that contains the error"
    )
    position: int = Field(
        ...,
        description="Character position of the error in the original text",
        ge=0
    )
    error_type: str = Field(
        ...,
        description="Type of spelling error detected",
        examples=["invalid_prefix_combination", "invalid_suffix", "encoding_error", "unknown_word"]
    )
    severity: str = Field(
        ...,
        description="Severity level of the error",
        examples=["critical", "error", "warning", "info"]
    )
    message: str | None = Field(
        None,
        description="Human-readable error message"
    )
    component: str | None = Field(
        None,
        description="Which syllable component has the error",
        examples=["prefix", "suffix", "superscript", "subscript"]
    )
    corpus_hit: bool | None = Field(
        None,
        description=(
            "Whether this syllable was found in the word corpus. "
            "True on a structural error means the Phase 1 rule may be a false positive. "
            "None means the corpus was not loaded."
        )
    )


class SpellCheckResponse(BaseModel):
    """Response containing spell check results."""
    
    text: str = Field(
        ...,
        description="The original text that was checked"
    )
    error_count: int = Field(
        ...,
        description="Total number of errors found",
        ge=0
    )
    errors: List[ErrorResponse] = Field(
        default_factory=list,
        description="List of errors found in the text"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "བོད་ཡིག་གི་སྐད་ཡིག",
                "error_count": 0,
                "errors": []
            }
        }


# --- PDF upload schemas ---

class PDFErrorResponse(BaseModel):
    """A spell error found in an uploaded PDF."""
    word: str
    page: int = Field(..., description="1-based page number", ge=1)
    error_type: str
    severity: str
    message: Optional[str] = None
    component: Optional[str] = None
    corpus_hit: Optional[bool] = None


class PDFUploadSyncResponse(BaseModel):
    """Response for small PDFs processed synchronously."""
    job_id: str
    page_count: int
    error_count: int
    errors: List[PDFErrorResponse]
    is_scanned: bool
    pdf_url: str
    docx_url: str


class PDFUploadAsyncResponse(BaseModel):
    """Response for large PDFs queued for async processing."""
    job_id: str
    page_count: int
    status: str = "pending"
    message: str


class JobStatusResponse(BaseModel):
    """Polling response for async job status."""
    job_id: str
    status: str          # pending | processing | completed | failed
    progress: int        # 0–100
    page_count: int
    error_count: Optional[int] = None
    error_message: Optional[str] = None
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None


class CorpusStatsResponse(BaseModel):
    """Statistics about the loaded word corpus."""
    available: bool = Field(
        ...,
        description="True if the word corpus is loaded and dictionary lookup is active"
    )
    word_count: int = Field(
        ...,
        description="Number of entries in the spelling_reference table",
        ge=0
    )
    syllable_count: int = Field(
        ...,
        description="Number of unique syllables extracted from all corpus entries",
        ge=0
    )
