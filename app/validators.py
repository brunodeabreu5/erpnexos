"""Input validation module for ERP Paraguay.

This module provides validation functions for user input to ensure
data integrity and prevent common security issues.
"""
import re
from typing import Tuple, Optional
from app.config import MIN_PASSWORD_LENGTH


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validate a username meets requirements.

    Username must be 3-50 characters, alphanumeric with underscores allowed.

    Args:
        username: The username to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, f"Username must be at least 3 characters"

    if len(username) > 50:
        return False, f"Username must be at most 50 characters"

    # Allow only alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"

    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """Validate a password meets minimum requirements.

    Password must be at least MIN_PASSWORD_LENGTH characters.
    For production, consider adding complexity requirements.

    Args:
        password: The password to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not password:
        return False, "Password is required"

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    # Optional: Add complexity requirements for production
    # if not re.search(r'[A-Z]', password):
    #     return False, "Password must contain at least one uppercase letter"
    # if not re.search(r'[a-z]', password):
    #     return False, "Password must contain at least one lowercase letter"
    # if not re.search(r'[0-9]', password):
    #     return False, "Password must contain at least one number"

    return True, None


def validate_product_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate a product name.

    Product name must be non-empty and at most 255 characters.

    Args:
        name: The product name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not name or not name.strip():
        return False, "Product name is required"

    if len(name.strip()) > 255:
        return False, "Product name must be at most 255 characters"

    return True, None


def validate_positive_number(value: float, field_name: str = "Value") -> Tuple[bool, Optional[str]]:
    """Validate that a number is positive (greater than zero).

    Args:
        value: The number to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        num_value = float(value)
        if num_value <= 0:
            return False, f"{field_name} must be greater than zero"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_non_negative_number(value: float, field_name: str = "Value") -> Tuple[bool, Optional[str]]:
    """Validate that a number is non-negative (zero or positive).

    Args:
        value: The number to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        num_value = float(value)
        if num_value < 0:
            return False, f"{field_name} cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_required_string(value: str, field_name: str = "Field", max_length: int = 255) -> Tuple[bool, Optional[str]]:
    """Validate that a string field is provided and within length limits.

    Args:
        value: The string value to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not value or not value.strip():
        return False, f"{field_name} is required"

    if len(value.strip()) > max_length:
        return False, f"{field_name} must be at most {max_length} characters"

    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate an email address format.

    Basic email validation - checks for @ symbol and basic structure.

    Args:
        email: The email address to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not email:
        return True, None  # Email is optional

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate a phone number.

    Accepts various formats with digits, spaces, hyphens, parentheses, and plus sign.

    Args:
        phone: The phone number to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not phone:
        return True, None  # Phone is optional

    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)

    # Check if it contains only digits and reasonable length
    if not cleaned.isdigit():
        return False, "Phone number must contain only digits"

    if len(cleaned) < 7 or len(cleaned) > 15:
        return False, "Phone number must be between 7 and 15 digits"

    return True, None


def validate_tax_id(tax_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a tax ID (RUC/CI).

    Accepts alphanumeric characters with basic validation.

    Args:
        tax_id: The tax ID to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not tax_id:
        return True, None  # Tax ID is optional

    # Remove spaces and hyphens
    cleaned = re.sub(r'[\s\-]', '', tax_id)

    if len(cleaned) < 5 or len(cleaned) > 20:
        return False, "Tax ID must be between 5 and 20 characters"

    # Allow alphanumeric characters
    if not re.match(r'^[a-zA-Z0-9]+$', cleaned):
        return False, "Tax ID can only contain letters and numbers"

    return True, None


def validate_sku(sku: str) -> Tuple[bool, Optional[str]]:
    """Validate a stock keeping unit (SKU).

    Args:
        sku: The SKU to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not sku:
        return True, None  # SKU is optional

    if len(sku) > 50:
        return False, "SKU must be at most 50 characters"

    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\-_]+$', sku):
        return False, "SKU can only contain letters, numbers, hyphens, and underscores"

    return True, None


def validate_category_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate a category name.

    Args:
        name: The category name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not name or not name.strip():
        return False, "Category name is required"

    if len(name.strip()) > 100:
        return False, "Category name must be at most 100 characters"

    return True, None


def validate_customer_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate a customer name.

    Args:
        name: The customer name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not name or not name.strip():
        return False, "Customer name is required"

    if len(name.strip()) > 255:
        return False, "Customer name must be at most 255 characters"

    return True, None


def validate_expense_category(category: str) -> Tuple[bool, Optional[str]]:
    """Validate an expense category.

    Args:
        category: The expense category to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    valid_categories = [
        'rent',          # aluguel
        'utilities',     # luz, água, gás, internet
        'salaries',      # salários
        'taxes',         # impostos
        'materials',     # materiais de escritório, limpeza
        'marketing',     # marketing e propaganda
        'maintenance',   # manutenção
        'shipping',      # frete e transporte
        'other'          # outros
    ]

    if not category or not category.strip():
        return False, "Expense category is required"

    category_lower = category.strip().lower()
    if category_lower not in valid_categories:
        return False, f"Invalid category. Must be one of: {', '.join(valid_categories)}"

    return True, None


def validate_payment_method_for_expense(method: str) -> Tuple[bool, Optional[str]]:
    """Validate a payment method for expenses.

    Args:
        method: The payment method to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not method or not method.strip():
        return True, None  # Optional for expenses

    valid_methods = ['cash', 'transfer', 'card', 'check', 'pix']
    method_lower = method.strip().lower()

    if method_lower not in valid_methods:
        return False, f"Payment method must be one of: {', '.join(valid_methods)}"

    return True, None


def validate_expense_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """Validate an expense amount.

    Args:
        amount: The amount to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return False, "Expense amount must be greater than zero"
        return True, None
    except (ValueError, TypeError):
        return False, "Expense amount must be a valid number"


def validate_quantity(quantity: float, field_name: str = "Quantity") -> Tuple[bool, Optional[str]]:
    """Validate that a quantity is positive.

    Args:
        quantity: The quantity to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        qty_value = float(quantity)
        if qty_value <= 0:
            return False, f"{field_name} must be greater than zero"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_sale_items(items: list) -> Tuple[bool, Optional[str]]:
    """Validate a list of sale items.

    Args:
        items: List of sale item dictionaries

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not items or len(items) == 0:
        return False, "Sale must have at least one item"

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item {i+1} must be a dictionary"

        # Check required fields
        if 'product_id' not in item:
            return False, f"Item {i+1} missing product_id"
        if 'quantity' not in item:
            return False, f"Item {i+1} missing quantity"
        if 'unit_price' not in item:
            return False, f"Item {i+1} missing unit_price"

        # Validate quantity
        is_valid, error = validate_quantity(item['quantity'], f"Item {i+1} quantity")
        if not is_valid:
            return False, error

        # Validate unit price
        is_valid, error = validate_positive_number(item['unit_price'], f"Item {i+1} unit_price")
        if not is_valid:
            return False, error

        # Validate discount if present
        if 'discount' in item and item['discount'] is not None:
            is_valid, error = validate_non_negative_number(item['discount'], f"Item {i+1} discount")
            if not is_valid:
                return False, error

    return True, None


def validate_payment_method(method: str) -> Tuple[bool, Optional[str]]:
    """Validate a payment method.

    Args:
        method: The payment method to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not method or not method.strip():
        return False, "Payment method is required"

    valid_methods = ['cash', 'transfer', 'card', 'credit']
    method_lower = method.strip().lower()

    if method_lower not in valid_methods:
        return False, f"Payment method must be one of: {', '.join(valid_methods)}"

    return True, None


def validate_discount(discount: float) -> Tuple[bool, Optional[str]]:
    """Validate a discount amount.

    Args:
        discount: The discount to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        discount_value = float(discount)
        if discount_value < 0:
            return False, "Discount cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, "Discount must be a valid number"
