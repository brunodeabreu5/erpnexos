"""Custom exceptions for ERP Paraguay.

This module provides a hierarchy of custom exceptions that allow for
specific error handling throughout the application.

Exception Hierarchy:
    ERPException
    ├── ValidationError
    │   ├── ValidationError
    │   └── BusinessRuleError
    ├── NotFoundError
    │   ├── CustomerNotFoundError
    │   ├── ProductNotFoundError
    │   ├── SaleNotFoundError
    │   └── SupplierNotFoundError
    ├── AuthenticationError
    │   ├── InvalidCredentialsError
    │   ├── AccountLockedError
    │   └── SessionExpiredError
    ├── AuthorizationError
    │   └── PermissionDeniedError
    └── PaymentError
        ├── InsufficientPaymentError
        └── OverpaymentError

Usage Example:
    try:
        customer = get_customer(customer_id)
    except CustomerNotFoundError:
        logger.warning(f"Customer {customer_id} not found")
        # Handle specific case
    except ERPException as e:
        logger.error(f"ERP error: {e}")
        # Handle general ERP errors
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ERPException(Exception):
    """Base exception for all ERP-related errors.

    All custom exceptions in the ERP system inherit from this class,
    allowing for broad error handling when needed.

    Attributes:
        message: Human-readable error description
        error_code: Optional machine-readable error code
        details: Optional dictionary with additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error description
            error_code: Optional machine-readable error code (e.g., 'CUS001')
            details: Optional dictionary with additional context
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Returns:
            Dictionary with error details
        """
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(ERPException):
    """Raised when input validation fails.

    Use this exception when user input or data doesn't meet validation rules.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.

        Args:
            message: Human-readable error description
            field: Optional field name that failed validation
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        if field:
            details = details or {}
            details['field'] = field
        super().__init__(message, error_code, details)


class BusinessRuleError(ERPException):
    """Raised when a business rule is violated.

    Use this exception when an operation would break business logic,
    such as selling items with insufficient stock.
    """

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize business rule error.

        Args:
            message: Human-readable error description
            rule_name: Optional name of the violated rule
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        if rule_name:
            details = details or {}
            details['rule'] = rule_name
        super().__init__(message, error_code, details)


# =============================================================================
# Not Found Errors
# =============================================================================

class NotFoundError(ERPException):
    """Base exception for resource-not-found errors."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Any] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize not found error.

        Args:
            resource_type: Type of resource (e.g., 'Customer', 'Product')
            resource_id: Optional ID of the resource
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
            details = details or {}
            details['resource_id'] = resource_id
        else:
            message = f"{resource_type} not found"

        super().__init__(message, error_code, details)


class CustomerNotFoundError(NotFoundError):
    """Raised when a customer is not found."""

    def __init__(self, customer_id: int):
        """Initialize customer not found error.

        Args:
            customer_id: ID of the customer
        """
        super().__init__('Customer', customer_id, 'CUS001')


class ProductNotFoundError(NotFoundError):
    """Raised when a product is not found."""

    def __init__(self, product_id: int):
        """Initialize product not found error.

        Args:
            product_id: ID of the product
        """
        super().__init__('Product', product_id, 'PRD001')


class SaleNotFoundError(NotFoundError):
    """Raised when a sale is not found."""

    def __init__(self, sale_id: int):
        """Initialize sale not found error.

        Args:
            sale_id: ID of the sale
        """
        super().__init__('Sale', sale_id, 'SAL001')


class SupplierNotFoundError(NotFoundError):
    """Raised when a supplier is not found."""

    def __init__(self, supplier_id: int):
        """Initialize supplier not found error.

        Args:
            supplier_id: ID of the supplier
        """
        super().__init__('Supplier', supplier_id, 'SUP001')


class CategoryNotFoundError(NotFoundError):
    """Raised when a category is not found."""

    def __init__(self, category_id: int):
        """Initialize category not found error.

        Args:
            category_id: ID of the category
        """
        super().__init__('Category', category_id, 'CAT001')


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(self, user_id: Optional[int] = None, username: Optional[str] = None):
        """Initialize user not found error.

        Args:
            user_id: Optional ID of the user
            username: Optional username of the user
        """
        details = {}
        if user_id:
            details['user_id'] = user_id
        if username:
            details['username'] = username

        identifier = user_id or username or 'Unknown'
        super().__init__('User', identifier, 'USR001', details)


# =============================================================================
# Authentication Errors
# =============================================================================

class AuthenticationError(ERPException):
    """Base exception for authentication failures."""

    def __init__(
        self,
        message: str,
        username: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication error.

        Args:
            message: Human-readable error description
            username: Optional username that failed authentication
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        if username:
            details = details or {}
            details['username'] = username
        super().__init__(message, error_code, details)


class InvalidCredentialsError(AuthenticationError):
    """Raised when username or password is invalid."""

    def __init__(self, username: Optional[str] = None):
        """Initialize invalid credentials error.

        Args:
            username: Optional username that failed authentication
        """
        super().__init__(
            'Invalid username or password',
            username,
            'AUTH001'
        )


class AccountLockedError(AuthenticationError):
    """Raised when an account is temporarily locked."""

    def __init__(self, username: str, remaining_minutes: int):
        """Initialize account locked error.

        Args:
            username: Username that is locked
            remaining_minutes: Minutes until account unlocks
        """
        details = {'remaining_minutes': remaining_minutes}
        super().__init__(
            f'Account temporarily locked. Try again in {remaining_minutes} minutes.',
            username,
            'AUTH002',
            details
        )


class SessionExpiredError(AuthenticationError):
    """Raised when a user session has expired."""

    def __init__(self, username: str):
        """Initialize session expired error.

        Args:
            username: Username with expired session
        """
        super().__init__(
            'Session has expired. Please log in again.',
            username,
            'AUTH003'
        )


# =============================================================================
# Authorization Errors
# =============================================================================

class AuthorizationError(ERPException):
    """Base exception for authorization failures."""

    def __init__(
        self,
        message: str,
        user_role: Optional[str] = None,
        required_permission: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authorization error.

        Args:
            message: Human-readable error description
            user_role: Optional role of the user
            required_permission: Optional permission that was required
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        details = details or {}
        if user_role:
            details['user_role'] = user_role
        if required_permission:
            details['required_permission'] = required_permission

        super().__init__(message, error_code, details)


class PermissionDeniedError(AuthorizationError):
    """Raised when user lacks permission for an action."""

    def __init__(self, action: str, user_role: str):
        """Initialize permission denied error.

        Args:
            action: Action that was denied
            user_role: Role of the user
        """
        super().__init__(
            f'Permission denied: {user_role} role cannot perform action: {action}',
            user_role,
            action,
            'AUTH001'
        )


# =============================================================================
# Payment Errors
# =============================================================================

class PaymentError(ERPException):
    """Base exception for payment-related errors."""

    def __init__(
        self,
        message: str,
        sale_id: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize payment error.

        Args:
            message: Human-readable error description
            sale_id: Optional ID of the sale
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        details = details or {}
        if sale_id:
            details['sale_id'] = sale_id
        super().__init__(message, error_code, details)


class InsufficientPaymentError(PaymentError):
    """Raised when payment amount is less than required."""

    def __init__(self, sale_id: int, amount_due: float, amount_paid: float):
        """Initialize insufficient payment error.

        Args:
            sale_id: ID of the sale
            amount_due: Amount required
            amount_paid: Amount provided
        """
        details = {
            'amount_due': amount_due,
            'amount_paid': amount_paid,
            'shortage': amount_due - amount_paid
        }
        super().__init__(
            f'Insufficient payment. Required: {amount_due:.2f}, Provided: {amount_paid:.2f}',
            sale_id,
            'PAY001',
            details
        )


class OverpaymentError(PaymentError):
    """Raised when payment amount exceeds balance due."""

    def __init__(self, sale_id: int, balance_due: float, payment_amount: float):
        """Initialize overpayment error.

        Args:
            sale_id: ID of the sale
            balance_due: Remaining balance
            payment_amount: Payment amount attempted
        """
        details = {
            'balance_due': balance_due,
            'payment_amount': payment_amount,
            'excess': payment_amount - balance_due
        }
        super().__init__(
            f'Payment exceeds balance due. Balance: {balance_due:.2f}, Payment: {payment_amount:.2f}',
            sale_id,
            'PAY002',
            details
        )


# =============================================================================
# Inventory Errors
# =============================================================================

class InsufficientStockError(BusinessRuleError):
    """Raised when attempting to sell more items than available in stock."""

    def __init__(self, product_name: str, requested: float, available: float):
        """Initialize insufficient stock error.

        Args:
            product_name: Name of the product
            requested: Quantity requested
            available: Quantity available
        """
        details = {
            'product': product_name,
            'requested': requested,
            'available': available,
            'shortage': requested - available
        }
        super().__init__(
            f'Insufficient stock for "{product_name}". Available: {available}, Requested: {requested}',
            'insufficient_stock',
            'INV001',
            details
        )


# =============================================================================
# Database Errors
# =============================================================================

class DatabaseError(ERPException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize database error.

        Args:
            message: Human-readable error description
            operation: Optional database operation that failed
            error_code: Optional machine-readable error code
            details: Optional dictionary with additional context
        """
        if operation:
            details = details or {}
            details['operation'] = operation
        super().__init__(message, error_code or 'DB001', details)


class DuplicateRecordError(ValidationError):
    """Raised when attempting to create a duplicate record."""

    def __init__(self, resource_type: str, field: str, value: str):
        """Initialize duplicate record error.

        Args:
            resource_type: Type of resource (e.g., 'Customer')
            field: Field that must be unique
            value: Value that already exists
        """
        details = {'field': field, 'value': value}
        super().__init__(
            f'{resource_type} with {field} "{value}" already exists',
            field,
            'DUP001',
            details
        )
