"""Sanitizer - Clean content before LLM exposure.

Provides content sanitization to:
- Remove sensitive information (PII, secrets, etc.)
- Normalize formatting
- Truncate to safe lengths
"""

import re
from dataclasses import dataclass


@dataclass
class SanitizeResult:
    """Result of sanitization.
    
    Attributes:
        content: Sanitized content.
        redactions: Number of redactions made.
        truncated: Whether content was truncated.
    """
    content: str
    redactions: int = 0
    truncated: bool = False


class Sanitizer:
    """Content sanitizer for LLM safety.
    
    Removes potential PII and sensitive information before
    sending content to LLMs.
    """
    
    # Patterns to redact
    PATTERNS = [
        # Email addresses
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        # Phone numbers (various formats)
        (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),
        # Social Security Numbers
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        # Credit card numbers (simplified)
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
        # API keys (common patterns)
        (r'\b(?:sk|pk|api)[-_]?[a-zA-Z0-9]{20,}\b', '[API_KEY]'),
        # Bearer tokens
        (r'\bBearer\s+[a-zA-Z0-9._-]+\b', '[TOKEN]'),
        # AWS access keys
        (r'\bAKIA[0-9A-Z]{16}\b', '[AWS_KEY]'),
        # Generic secrets in env format
        (r'(?i)(?:password|secret|token|key)\s*[=:]\s*[^\s]+', '[SECRET]'),
    ]
    
    def __init__(self, max_length: int = 10000):
        """Initialize sanitizer.
        
        Args:
            max_length: Maximum content length after sanitization.
        """
        self.max_length = max_length
        self._compiled_patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.PATTERNS
        ]
    
    def sanitize(self, content: str) -> SanitizeResult:
        """Sanitize content.
        
        Args:
            content: Raw content to sanitize.
            
        Returns:
            SanitizeResult with cleaned content.
        """
        redactions = 0
        result = content
        
        # Apply redaction patterns
        for pattern, replacement in self._compiled_patterns:
            result, count = pattern.subn(replacement, result)
            redactions += count
        
        # Truncate if necessary
        truncated = False
        if len(result) > self.max_length:
            result = result[:self.max_length] + "\n... [TRUNCATED]"
            truncated = True
        
        return SanitizeResult(
            content=result,
            redactions=redactions,
            truncated=truncated,
        )
    
    def sanitize_for_llm(self, content: str) -> str:
        """Convenience method for LLM sanitization.
        
        Args:
            content: Raw content.
            
        Returns:
            Sanitized content string.
        """
        return self.sanitize(content).content
