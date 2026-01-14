"""
Custom exceptions for document generator.

Defines specific exception types for different error scenarios.
"""


class DocumentGeneratorError(Exception):
    """Base exception for document generator."""
    pass


class ParseError(DocumentGeneratorError):
    """Raised when content parsing fails."""
    pass


class GenerationError(DocumentGeneratorError):
    """Raised when document generation fails."""
    pass


class ValidationError(DocumentGeneratorError):
    """Raised when document validation fails."""
    pass


class UnsupportedFormatError(DocumentGeneratorError):
    """Raised when input or output format is not supported."""
    pass


class FileNotFoundError(DocumentGeneratorError):
    """Raised when input file is not found."""
    pass
