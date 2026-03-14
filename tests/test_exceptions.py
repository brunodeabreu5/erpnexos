"""Unit tests for custom exceptions.

Tests all custom exception classes and their functionality.
"""
import pytest
from app.exceptions import (
    ERPException,
    ValidationError,
    BusinessRuleError,
    NotFoundError,
    CustomerNotFoundError,
    ProductNotFoundError,
    SaleNotFoundError,
    SupplierNotFoundError,
    CategoryNotFoundError,
    UserNotFoundError,
    AuthenticationError,
    InvalidCredentialsError,
    AccountLockedError,
    SessionExpiredError,
    AuthorizationError,
    PermissionDeniedError,
    PaymentError,
    InsufficientPaymentError,
    OverpaymentError,
    InsufficientStockError,
    DatabaseError,
    DuplicateRecordError
)


class TestERPException:
    """Tests for base ERPException class."""

    def test_create_basic_exception(self):
        """Test creating a basic ERP exception."""
        exc = ERPException("Test error")

        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code is None
        assert exc.details == {}

    def test_exception_with_error_code(self):
        """Test exception with error code."""
        exc = ERPException("Test error", error_code="ERR001")

        assert exc.error_code == "ERR001"
        assert "ERR001" in str(exc)

    def test_exception_with_details(self):
        """Test exception with details dictionary."""
        details = {"field": "email", "value": "test@example.com"}
        exc = ERPException("Test error", details=details)

        assert exc.details == details

    def test_to_dict(self):
        """Test exception to_dict method."""
        exc = ERPException(
            "Test error",
            error_code="ERR001",
            details={"key": "value"}
        )

        result = exc.to_dict()

        assert result['error'] == 'ERPException'
        assert result['message'] == 'Test error'
        assert result['error_code'] == 'ERR001'
        assert result['details'] == {'key': 'value'}


class TestValidationError:
    """Tests for ValidationError class."""

    def test_validation_error_with_field(self):
        """Test validation error with field specified."""
        exc = ValidationError(
            "Email is required",
            field="email"
        )

        assert exc.details['field'] == 'email'
        assert 'email' in str(exc).lower()

    def test_validation_error_to_dict(self):
        """Test validation error to_dict includes field."""
        exc = ValidationError("Invalid input", field="username")

        result = exc.to_dict()

        assert result['details']['field'] == 'username'


class TestBusinessRuleError:
    """Tests for BusinessRuleError class."""

    def test_business_rule_error_with_rule_name(self):
        """Test business rule error with rule name."""
        exc = BusinessRuleError(
            "Cannot sell item with insufficient stock",
            rule_name="insufficient_stock"
        )

        assert exc.details['rule'] == 'insufficient_stock'


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_not_found_error_with_resource_type(self):
        """Test not found error with resource type."""
        exc = NotFoundError("Product", resource_id=999)

        assert "Product" in str(exc)
        assert "999" in str(exc)

    def test_not_found_error_to_dict(self):
        """Test not found error to_dict includes resource_id."""
        exc = NotFoundError("Customer", resource_id=123)

        result = exc.to_dict()

        assert result['details']['resource_id'] == 123


class TestCustomerNotFoundError:
    """Tests for CustomerNotFoundError class."""

    def test_customer_not_found(self):
        """Test customer not found exception."""
        exc = CustomerNotFoundError(456)

        assert "Customer" in str(exc)
        assert "456" in str(exc)
        assert exc.error_code == 'CUS001'

    def test_customer_not_found_inheritance(self):
        """Test CustomerNotFoundError inherits from NotFoundError."""
        exc = CustomerNotFoundError(1)

        assert isinstance(exc, NotFoundError)
        assert isinstance(exc, ERPException)


class TestProductNotFoundError:
    """Tests for ProductNotFoundError class."""

    def test_product_not_found(self):
        """Test product not found exception."""
        exc = ProductNotFoundError(789)

        assert "Product" in str(exc)
        assert "789" in str(exc)
        assert exc.error_code == 'PRD001'


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_authentication_error_with_username(self):
        """Test authentication error includes username."""
        exc = AuthenticationError(
            "Authentication failed",
            username="testuser"
        )

        assert exc.details['username'] == 'testuser'

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError."""
        exc = InvalidCredentialsError("testuser")

        assert "Invalid" in str(exc)
        assert exc.error_code == 'AUTH001'

    def test_account_locked_error(self):
        """Test AccountLockedError includes remaining time."""
        exc = AccountLockedError("testuser", remaining_minutes=15)

        assert "locked" in str(exc).lower()
        assert exc.details['remaining_minutes'] == 15

    def test_session_expired_error(self):
        """Test SessionExpiredError."""
        exc = SessionExpiredError("testuser")

        assert "expired" in str(exc).lower()


class TestInsufficientStockError:
    """Tests for InsufficientStockError class."""

    def test_insufficient_stock_error(self):
        """Test insufficient stock error includes details."""
        exc = InsufficientStockError(
            product_name="Widget",
            requested=50,
            available=10
        )

        assert "Insufficient stock" in str(exc)
        assert exc.details['product'] == 'Widget'
        assert exc.details['requested'] == 50
        assert exc.details['available'] == 10
        assert exc.details['shortage'] == 40

    def test_insufficient_stock_error_inheritance(self):
        """Test InsufficientStockError inherits from BusinessRuleError."""
        exc = InsufficientStockError("Product", 10, 5)

        assert isinstance(exc, BusinessRuleError)


class TestPaymentError:
    """Tests for PaymentError class."""

    def test_insufficient_payment_error(self):
        """Test InsufficientPaymentError."""
        exc = InsufficientPaymentError(
            sale_id=1,
            amount_due=100.0,
            amount_paid=50.0
        )

        assert "Insufficient payment" in str(exc)
        assert exc.details['amount_due'] == 100.0
        assert exc.details['amount_paid'] == 50.0
        assert exc.details['shortage'] == 50.0

    def test_overpayment_error(self):
        """Test OverpaymentError."""
        exc = OverpaymentError(
            sale_id=1,
            balance_due=100.0,
            payment_amount=150.0
        )

        assert "exceeds balance" in str(exc).lower()
        assert exc.details['balance_due'] == 100.0
        assert exc.details['payment_amount'] == 150.0
        assert exc.details['excess'] == 50.0


class TestDatabaseError:
    """Tests for DatabaseError class."""

    def test_database_error_with_operation(self):
        """Test database error includes operation name."""
        exc = DatabaseError(
            "Query failed",
            operation="SELECT * FROM products"
        )

        assert exc.details['operation'] == "SELECT * FROM products"


class TestDuplicateRecordError:
    """Tests for DuplicateRecordError class."""

    def test_duplicate_record_error(self):
        """Test duplicate record error includes field and value."""
        exc = DuplicateRecordError(
            resource_type="Customer",
            field="email",
            value="test@example.com"
        )

        assert "already exists" in str(exc).lower()
        assert exc.details['field'] == 'email'
        assert exc.details['value'] == 'test@example.com'


class TestExceptionChaining:
    """Tests for exception chaining and context."""

    def test_raise_and_catch_custom_exception(self):
        """Test raising and catching custom exceptions."""
        with pytest.raises(CustomerNotFoundError) as exc_info:
            raise CustomerNotFoundError(123)

        assert "Customer" in str(exc_info.value)
        assert "123" in str(exc_info.value)

    def test_exception_in_context_manager(self):
        """Test using exceptions with context managers."""
        try:
            raise ValidationError("Invalid input", field="username")
        except ValidationError as e:
            assert e.details['field'] == 'username'
            assert e.to_dict()['error'] == 'ValidationError'


class TestErrorCodeConsistency:
    """Tests that error codes follow expected patterns."""

    def test_all_not_found_errors_have_codes(self):
        """Test that all NotFoundError subclasses have error codes."""
        exceptions_to_test = [
            (CustomerNotFoundError, 'CUS001'),
            (ProductNotFoundError, 'PRD001'),
            (SaleNotFoundError, 'SAL001'),
            (SupplierNotFoundError, 'SUP001'),
            (CategoryNotFoundError, 'CAT001'),
            (UserNotFoundError, 'USR001')
        ]

        for exc_class, expected_code in exceptions_to_test:
            exc = exc_class(1)
            assert exc.error_code == expected_code

    def test_payment_errors_have_codes(self):
        """Test that payment errors have proper codes."""
        exc1 = InsufficientPaymentError(1, 100, 50)
        exc2 = OverpaymentError(1, 100, 150)

        assert exc1.error_code == 'PAY001'
        assert exc2.error_code == 'PAY002'


class TestExceptionMessages:
    """Tests that exception messages are user-friendly."""

    def test_messages_are_informative(self):
        """Test that exception messages provide useful information."""
        exceptions = [
            CustomerNotFoundError(1),
            ProductNotFoundError(2),
            InsufficientStockError("Widget", 10, 5),
            InvalidCredentialsError("user")
        ]

        for exc in exceptions:
            message = str(exc)
            assert len(message) > 10  # Not too short
            assert message is not None  # Not empty
            assert "error" not in message.lower()  # No generic "error" word

    def test_messages_do_not_leak_sensitive_info(self):
        """Test that error messages don't leak sensitive information."""
        # Password-related errors should not include the password
        exc = InvalidCredentialsError("testuser")

        message = str(exc)
        assert "password" not in message.lower()
        # Should be generic
        assert "username or password" in message.lower() or "invalid" in message.lower()
