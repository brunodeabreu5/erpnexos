"""Unit tests for the validators module.

Tests all validation functions to ensure they properly validate input
and return appropriate error messages.
"""
import pytest
from app.validators import (
    validate_username,
    validate_password,
    validate_product_name,
    validate_positive_number,
    validate_non_negative_number,
    validate_required_string,
    validate_email,
)


class TestValidateUsername:
    """Tests for validate_username function."""

    def test_valid_username(self):
        """Test that valid usernames are accepted."""
        assert validate_username("admin") == (True, None)
        assert validate_username("user123") == (True, None)
        assert validate_username("test_user") == (True, None)
        assert validate_username("ABC") == (True, None)
        assert validate_username("a" * 50) == (True, None)

    def test_empty_username(self):
        """Test that empty usernames are rejected."""
        assert validate_username("") == (False, "Username is required")
        assert validate_username(None) == (False, "Username is required")

    def test_short_username(self):
        """Test that usernames shorter than 3 characters are rejected."""
        assert validate_username("ab") == (False, "Username must be at least 3 characters")
        assert validate_username("a") == (False, "Username must be at least 3 characters")

    def test_long_username(self):
        """Test that usernames longer than 50 characters are rejected."""
        assert validate_username("a" * 51) == (False, "Username must be at most 50 characters")

    def test_invalid_characters(self):
        """Test that usernames with invalid characters are rejected."""
        assert validate_username("user@name") == (False, "Username can only contain letters, numbers, and underscores")
        assert validate_username("user name") == (False, "Username can only contain letters, numbers, and underscores")
        assert validate_username("user-name") == (False, "Username can only contain letters, numbers, and underscores")


class TestValidatePassword:
    """Tests for validate_password function."""

    def test_valid_password(self):
        """Test that valid passwords are accepted."""
        assert validate_password("password123") == (True, None)
        assert validate_password("123456") == (True, None)
        assert validate_password("a" * 100) == (True, None)

    def test_empty_password(self):
        """Test that empty passwords are rejected."""
        assert validate_password("") == (False, "Password is required")
        assert validate_password(None) == (False, "Password is required")

    def test_short_password(self):
        """Test that passwords shorter than MIN_PASSWORD_LENGTH are rejected."""
        assert validate_password("12345") == (False, "Password must be at least 6 characters")


class TestValidateProductName:
    """Tests for validate_product_name function."""

    def test_valid_product_name(self):
        """Test that valid product names are accepted."""
        assert validate_product_name("Product A") == (True, None)
        assert validate_product_name("Test Product") == (True, None)
        assert validate_product_name("a" * 255) == (True, None)

    def test_empty_product_name(self):
        """Test that empty product names are rejected."""
        assert validate_product_name("") == (False, "Product name is required")
        assert validate_product_name(None) == (False, "Product name is required")
        assert validate_product_name("   ") == (False, "Product name is required")

    def test_long_product_name(self):
        """Test that product names longer than 255 characters are rejected."""
        assert validate_product_name("a" * 256) == (False, "Product name must be at most 255 characters")


class TestValidatePositiveNumber:
    """Tests for validate_positive_number function."""

    def test_valid_positive_numbers(self):
        """Test that valid positive numbers are accepted."""
        assert validate_positive_number(1.0) == (True, None)
        assert validate_positive_number(100) == (True, None)
        assert validate_positive_number(0.01) == (True, None)
        assert validate_positive_number("50.5") == (True, None)

    def test_zero_and_negative(self):
        """Test that zero and negative numbers are rejected."""
        result, error = validate_positive_number(0)
        assert result is False
        assert "greater than zero" in error

        result, error = validate_positive_number(-1)
        assert result is False
        assert "greater than zero" in error

    def test_invalid_numbers(self):
        """Test that non-numeric values are rejected."""
        result, error = validate_positive_number("abc")
        assert result is False
        assert "valid number" in error

        result, error = validate_positive_number(None)
        assert result is False
        assert "valid number" in error

    def test_custom_field_name(self):
        """Test that custom field names appear in error messages."""
        result, error = validate_positive_number(-1, "Price")
        assert result is False
        assert "Price" in error


class TestValidateNonNegativeNumber:
    """Tests for validate_non_negative_number function."""

    def test_valid_non_negative_numbers(self):
        """Test that valid non-negative numbers are accepted."""
        assert validate_non_negative_number(0) == (True, None)
        assert validate_non_negative_number(1.0) == (True, None)
        assert validate_non_negative_number(100) == (True, None)
        assert validate_non_negative_number("50.5") == (True, None)

    def test_negative_numbers(self):
        """Test that negative numbers are rejected."""
        result, error = validate_non_negative_number(-1)
        assert result is False
        assert "cannot be negative" in error

        result, error = validate_non_negative_number(-0.01)
        assert result is False
        assert "cannot be negative" in error

    def test_invalid_numbers(self):
        """Test that non-numeric values are rejected."""
        result, error = validate_non_negative_number("abc")
        assert result is False
        assert "valid number" in error


class TestValidateRequiredString:
    """Tests for validate_required_string function."""

    def test_valid_strings(self):
        """Test that valid non-empty strings are accepted."""
        assert validate_required_string("test") == (True, None)
        assert validate_required_string("  test  ") == (True, None)
        assert validate_required_string("a" * 100) == (True, None)

    def test_empty_strings(self):
        """Test that empty strings are rejected."""
        assert validate_required_string("") == (False, "Field is required")
        assert validate_required_string(None) == (False, "Field is required")
        assert validate_required_string("   ") == (False, "Field is required")

    def test_max_length(self):
        """Test that strings exceeding max length are rejected."""
        result, error = validate_required_string("a" * 101, "Test", max_length=100)
        assert result is False
        assert "at most 100 characters" in error

    def test_custom_field_name(self):
        """Test that custom field names appear in error messages."""
        assert validate_required_string("", "Custom Field") == (False, "Custom Field is required")


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_emails(self):
        """Test that valid email addresses are accepted."""
        assert validate_email("user@example.com") == (True, None)
        assert validate_email("test.user@domain.co.uk") == (True, None)
        assert validate_email("user+tag@example.org") == (True, None)

    def test_empty_email(self):
        """Test that empty emails are rejected."""
        assert validate_email("") == (False, "Email is required")
        assert validate_email(None) == (False, "Email is required")

    def test_invalid_emails(self):
        """Test that invalid email formats are rejected."""
        assert validate_email("invalid") == (False, "Invalid email format")
        assert validate_email("@example.com") == (False, "Invalid email format")
        assert validate_email("user@") == (False, "Invalid email format")
        assert validate_email("user@domain") == (False, "Invalid email format")
        assert validate_email("user domain@com") == (False, "Invalid email format")
