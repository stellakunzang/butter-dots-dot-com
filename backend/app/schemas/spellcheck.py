"""
Pydantic schemas for spell check API requests and responses.
"""
from typing import List
from pydantic import BaseModel, Field


class SpellCheckRequest(BaseModel):
    """Request to check Tibetan text for spelling errors."""
    
    text: str = Field(
        ...,
        description="Tibetan text to check for spelling errors",
        min_length=1,
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
        examples=["invalid_prefix_combination", "invalid_suffix", "encoding_error"]
    )
    severity: str = Field(
        ...,
        description="Severity level of the error",
        examples=["critical", "error", "info"]
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
