"""Type definitions for ERP Paraguay.

This module provides common type aliases used throughout the application
to ensure consistency and improve code documentation.
"""
from typing import TypeVar, Tuple, Optional

# Generic type variable
T = TypeVar('T')

# Standard result type for operations that can fail
# Format: (success: bool, error_message: Optional[str], data: Optional[T])
# - success: True if operation succeeded, False otherwise
# - error_message: None if success, error description if failed
# - data: Result data if success, None if failed (or success with no data)
Result = Tuple[bool, Optional[str], Optional[T]]

# Simple validation result type (no data)
# Format: (is_valid: bool, error_message: Optional[str])
ValidationResult = Tuple[bool, Optional[str]]


class ResultError(Exception):
    """Exception raised when an operation returns a failed Result.

    This can be used to convert Result types to exceptions when needed.
    """

    def __init__(self, message: str):
        """Initialize the exception.

        Args:
            message: The error message from the failed Result
        """
        self.message = message
        super().__init__(message)


def success(data: Optional[T] = None) -> Result[T]:
    """Create a successful Result.

    Args:
        data: Optional data to return

    Returns:
        Result tuple indicating success

    Example:
        return success(product)  # Returns (True, None, product)
        return success()  # Returns (True, None, None)
    """
    return True, None, data


def failure(error_message: str) -> Result:
    """Create a failed Result.

    Args:
        error_message: Description of the failure

    Returns:
        Result tuple indicating failure

    Example:
        return failure("Product not found")  # Returns (False, "Product not found", None)
    """
    return False, error_message, None


def validate_result(result: Result[T]) -> T:
    """Validate a Result and raise an exception if it failed.

    This is useful when you want to use Result types but raise exceptions
    for error handling in specific cases.

    Args:
        result: The Result tuple to validate

    Returns:
        The data from the Result if successful

    Raises:
        ResultError: If the Result indicates failure

    Example:
        product = validate_result(get_product(1))  # Returns product or raises ResultError
    """
    success, error_message, data = result
    if not success:
        raise ResultError(error_message or "Unknown error")
    return data  # type: ignore
