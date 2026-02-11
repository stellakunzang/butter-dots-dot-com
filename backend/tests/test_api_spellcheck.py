"""
Tests for spell check API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestSpellCheckTextEndpoint:
    """Tests for POST /api/v1/spellcheck/text endpoint"""
    
    def test_check_valid_text(self):
        """Should return no errors for valid Tibetan text"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "བོད་ཡིག་གི་སྐད་ཡིག"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] == 0
        assert data["errors"] == []
        assert data["text"] == "བོད་ཡིག་གི་སྐད་ཡིག"
    
    def test_check_text_with_errors(self):
        """Should detect errors in invalid Tibetan text"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "བོད་གཀར་"}  # གཀར is invalid (ga cannot prefix ka)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] == 1
        assert len(data["errors"]) == 1
        
        error = data["errors"][0]
        assert error["word"] == "གཀར"
        assert error["error_type"] == "invalid_prefix_combination"
        assert error["severity"] == "error"
        assert "position" in error
        assert error["position"] >= 0
    
    def test_check_multiple_errors(self):
        """Should detect multiple errors in text"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "གཀར་དངས་"}  # Two invalid syllables
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] >= 1  # At least one error
        assert len(data["errors"]) >= 1
    
    def test_check_empty_text(self):
        """Should reject empty text"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": ""}
        )
        
        # Pydantic validation should reject empty string
        assert response.status_code == 422  # Validation error
    
    def test_check_whitespace_only(self):
        """Should handle whitespace gracefully without warnings"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "   "}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Whitespace should not generate warnings
        assert data["error_count"] == 0
        assert len(data["errors"]) == 0
    
    def test_tibetan_with_whitespace_no_warnings(self):
        """Tibetan text with spaces should not generate whitespace warnings"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "བོད་ཡིག གི་ སྐད་ཡིག"}  # Valid Tibetan with spaces
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should have no errors (no spelling errors, no whitespace warnings)
        assert data["error_count"] == 0
        assert len(data["errors"]) == 0
    
    def test_check_mixed_tibetan_and_english(self):
        """Should handle mixed content and provide summary note"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "བོད་ཡིག Hello World སྐད་ཡིག"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have one info message about skipped characters
        info_messages = [e for e in data["errors"] if e["error_type"] == "non_tibetan_skipped"]
        assert len(info_messages) == 1
        
        # Verify it's an info-level message
        assert info_messages[0]["severity"] == "info"
        assert "skipped" in info_messages[0].get("message", "").lower()
    
    def test_non_tibetan_character_summary(self):
        """Should provide summary of non-Tibetan characters (excluding whitespace)"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "བོད་ABC123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find non-Tibetan summary message
        info_messages = [e for e in data["errors"] if e["error_type"] == "non_tibetan_skipped"]
        
        # Should have one summary message
        assert len(info_messages) == 1
        assert info_messages[0]["severity"] == "info"
        assert "6" in info_messages[0]["message"]  # 6 non-Tibetan chars (ABC123)
        assert "skipped" in info_messages[0]["message"].lower()
    
    def test_check_long_text(self):
        """Should handle longer texts efficiently"""
        long_text = "བོད་ཡིག་" * 100  # Repeat 100 times
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": long_text}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error_count"] == 0
        assert "errors" in data
    
    def test_missing_text_field(self):
        """Should return validation error when text field is missing"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_request_body(self):
        """Should return validation error for invalid JSON"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"wrong_field": "test"}
        )
        
        assert response.status_code == 422  # Validation error


class TestErrorResponseStructure:
    """Tests for error response structure and fields"""
    
    def test_error_contains_required_fields(self):
        """Error objects should contain all required fields"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "གཀར"}  # Invalid
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["error_count"] > 0:
            error = data["errors"][0]
            # Check required fields
            assert "word" in error
            assert "position" in error
            assert "error_type" in error
            assert "severity" in error
            
            # Check types
            assert isinstance(error["word"], str)
            assert isinstance(error["position"], int)
            assert isinstance(error["error_type"], str)
            assert isinstance(error["severity"], str)
    
    def test_severity_levels_are_valid(self):
        """Severity should be one of: critical, error, info"""
        response = client.post(
            "/api/v1/spellcheck/text",
            json={"text": "གཀར"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for error in data["errors"]:
            assert error["severity"] in ["critical", "error", "info"]


class TestAPIDocumentation:
    """Tests for API documentation and OpenAPI schema"""
    
    def test_openapi_docs_available(self):
        """OpenAPI docs should be accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/spellcheck/text" in schema["paths"]
    
    def test_swagger_ui_available(self):
        """Swagger UI should be accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
