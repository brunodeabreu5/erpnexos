"""Pytest configuration and fixtures for ERP Paraguay tests.

This module provides shared fixtures and configuration for all test modules.
"""
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # Use in-memory SQLite for tests
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce logging noise in tests
os.environ["ENVIRONMENT"] = "test"
os.environ["ADMIN_PASSWORD"] = "TestAdminPassword123"
os.environ["COMPANY_NAME"] = "Test Company"
os.environ["COMPANY_TAX_ID"] = "12345678-9"
os.environ["TAX_RATE"] = "0.10"


@pytest.fixture
def test_password():
    """Fixture providing a test password."""
    return "TestPassword123"


@pytest.fixture
def test_username():
    """Fixture providing a test username."""
    return "testuser"


@pytest.fixture
def test_email():
    """Fixture providing a test email."""
    return "test@example.com"


@pytest.fixture
def test_phone():
    """Fixture providing a test phone number."""
    return "+595 21 123 456"


@pytest.fixture
def test_address():
    """Fixture providing a test address."""
    return "123 Test Street, Test City"


@pytest.fixture
def test_tax_id():
    """Fixture providing a test tax ID."""
    return "12345678-9"


@pytest.fixture
def test_product_data():
    """Fixture providing test product data."""
    return {
        "name": "Test Product",
        "sku": "TEST-001",
        "price": Decimal("99.99"),
        "cost_price": Decimal("50.00"),
        "stock": Decimal("50"),
        "reorder_point": Decimal("10"),
        "category_id": 1
    }


@pytest.fixture
def test_customer_data():
    """Fixture providing test customer data."""
    return {
        "name": "Test Customer",
        "email": "customer@example.com",
        "phone": "+595 21 111 222",
        "address": "456 Customer Ave",
        "tax_id": "98765432-1"
    }


@pytest.fixture
def test_supplier_data():
    """Fixture providing test supplier data."""
    return {
        "name": "Test Supplier",
        "contact_person": "John Doe",
        "email": "supplier@example.com",
        "phone": "+595 21 333 444",
        "address": "789 Supplier St",
        "tax_id": "11223344-5"
    }


@pytest.fixture
def test_category_data():
    """Fixture providing test category data."""
    return {
        "name": "Test Category",
        "description": "A test category for products"
    }


@pytest.fixture
def test_sale_items_data():
    """Fixture providing test sale items data."""
    return [
        {
            "product_id": 1,
            "quantity": 2,
            "unit_price": Decimal("99.99"),
            "discount": 0
        },
        {
            "product_id": 2,
            "quantity": 1,
            "unit_price": Decimal("49.99"),
            "discount": Decimal("5.00")
        }
    ]


@pytest.fixture
def mock_db_session():
    """Fixture providing a mock database session."""
    mock_db = Mock()
    mock_db.commit = Mock()
    mock_db.rollback = Mock()
    mock_db.flush = Mock()
    mock_db.refresh = Mock()
    return mock_db


@pytest.fixture
def mock_customer():
    """Fixture providing a mock customer object."""
    customer = Mock()
    customer.id = 1
    customer.name = "Test Customer"
    customer.email = "customer@example.com"
    customer.phone = "+595 21 111 222"
    customer.address = "456 Customer Ave"
    customer.tax_id = "98765432-1"
    customer.balance = Decimal("0")
    customer.is_active = True
    return customer


@pytest.fixture
def mock_product():
    """Fixture providing a mock product object."""
    product = Mock()
    product.id = 1
    product.name = "Test Product"
    product.sku = "TEST-001"
    product.price = Decimal("99.99")
    product.cost_price = Decimal("50.00")
    product.stock = Decimal("50")
    product.reorder_point = Decimal("10")
    product.category_id = 1
    product.is_active = True
    return product


@pytest.fixture
def mock_category():
    """Fixture providing a mock category object."""
    category = Mock()
    category.id = 1
    category.name = "Test Category"
    category.description = "A test category"
    category.is_active = True
    return category


@pytest.fixture
def mock_user():
    """Fixture providing a mock user object."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.full_name = "Test User"
    user.email = "test@example.com"
    user.role = "admin"
    user.is_active = True
    user.hashed_password = "$2b$12$test_hashed_password"
    return user


@pytest.fixture
def mock_sale():
    """Fixture providing a mock sale object."""
    sale = Mock()
    sale.id = 1
    sale.customer_id = 1
    sale.subtotal = Decimal("250.00")
    sale.tax_amount = Decimal("25.00")
    sale.discount_amount = Decimal("0")
    sale.total = Decimal("275.00")
    sale.payment_method = "cash"
    sale.payment_status = "paid"
    sale.status = "completed"
    sale.notes = None
    sale.sale_date = datetime.now()
    return sale


@pytest.fixture
def future_date():
    """Fixture providing a date 30 days in the future."""
    return datetime.now() + timedelta(days=30)


@pytest.fixture
def past_date():
    """Fixture providing a date 30 days in the past."""
    return datetime.now() - timedelta(days=30)
