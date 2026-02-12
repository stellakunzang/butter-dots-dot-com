"""
SpellError -- a spelling error found during validation.
"""
from dataclasses import dataclass


@dataclass
class SpellError:
    """
    A spelling error found during validation.

    Attributes:
        error_type: Machine-readable error category
        message: Human-readable explanation
        severity: 'critical', 'error', or 'info'
        component: Which syllable component triggered the error
    """
    error_type: str
    message: str
    severity: str
    component: str

    def to_dict(self) -> dict:
        """Convert to dictionary format for backwards compatibility."""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'severity': self.severity,
            'component': self.component,
        }
