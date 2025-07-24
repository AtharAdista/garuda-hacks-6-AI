"""
Exceptions for Gemini API services.
"""

from typing import Optional


class GeminiServiceException(Exception):
    """Base exception for Gemini API services."""

    def __init__(self, message: str, status_code: int = 400):
        """Initialize the exception.

        Args:
            message: The error message.
            status_code: The HTTP status code.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class GeminiAPIKeyMissingError(GeminiServiceException):
    """Exception raised when the Gemini API key is missing."""

    def __init__(self):
        """Initialize the exception."""
        super().__init__(
            message="Gemini API key is missing. Set the GOOGLE_API_KEY environment variable.",
            status_code=500,
        )


class GeminiAPIError(GeminiServiceException):
    """Exception raised when the Gemini API returns an error."""

    def __init__(self, message: str, status_code: int = 500):  # pragma: no cover
        """Initialize the exception.

        Args:
            message: The error message.
            status_code: The HTTP status code.
        """
        super().__init__(
            message=f"Gemini API error: {message}", status_code=status_code
        )


class GeminiParsingError(GeminiServiceException):
    """Exception raised when parsing the Gemini API response fails."""

    def __init__(self, message: str, response: Optional[str] = None):
        """Initialize the exception.

        Args:
            message: The error message.
            response: The raw response that failed to parse.
        """
        error_message = f"Failed to parse Gemini API response: {message}"
        if response:  # pragma: no cover
            error_message += (
                f"\nRaw response: {response[:100]}..."
                if len(response) > 100
                else f"\nRaw response: {response}"
            )

        super().__init__(message=error_message, status_code=422)


class InvalidImageError(GeminiServiceException):
    """Exception raised when the provided image is invalid."""

    def __init__(self, message: str = "Invalid image provided"):  # pragma: no cover
        """Initialize the exception.

        Args:
            message: The error message.
        """
        super().__init__(message=message, status_code=400)
