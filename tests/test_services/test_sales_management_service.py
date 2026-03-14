"""Unit tests for the sales management service module.

Tests sale creation, cancellation, payment processing, and business logic.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
from app.services.sales_management_service import (
    create_sale,
    get_sale_by_id,
    list_sales,
    cancel_sale,
    add_payment,
    get_sales_summary,
    validate_positive_number
)


class TestCreateSale:
    """Tests for create_sale function."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_create_sale_success_cash(self, mock_get_db_session, test_sale_items_data):
        """Test successful cash sale creation."""
        # Setup mocks
        mock_customer = Mock(id=1, name="Test Customer", balance=Decimal("0"))
        mock_product1 = Mock(id=1, name="Product 1", stock=Decimal("100"), is_active=True)
        mock_product2 = Mock(id=2, name="Product 2", stock=Decimal("50"), is_active=True)

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,  # Customer exists
            mock_product1,  # Product 1 check
            mock_product2   # Product 2 check
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, sale_id = create_sale(
            customer_id=1,
            items=test_sale_items_data,
            payment_method="cash",
            discount=0
        )

        assert success is True
        assert error is None
        assert sale_id is not None
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    @patch('app.services.sales_management_service.get_db_session')
    def test_create_sale_credit_sale(self, mock_get_db_session, test_sale_items_data):
        """Test credit sale creation updates customer balance."""
        mock_customer = Mock(id=1, name="Test Customer", balance=Decimal("0"))
        mock_product = Mock(id=1, name="Product 1", stock=Decimal("100"), is_active=True)

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_product,
            mock_product
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, sale_id = create_sale(
            customer_id=1,
            items=test_sale_items_data[:1],
            payment_method="credit",
            discount=0
        )

        assert success is True
        # Customer balance should be updated
        assert mock_customer.balance > 0

    @patch('app.services.sales_management_service.get_db_session')
    def test_create_sale_insufficient_stock(self, mock_get_db_session, test_sale_items_data):
        """Test sale creation fails with insufficient stock."""
        mock_customer = Mock(id=1, name="Test Customer")
        mock_product = Mock(id=1, name="Product 1", stock=Decimal("1"), is_active=True)

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_product
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Try to sell more than available
        items = [{
            "product_id": 1,
            "quantity": 10,
            "unit_price": Decimal("99.99"),
            "discount": 0
        }]

        success, error, sale_id = create_sale(
            customer_id=1,
            items=items,
            payment_method="cash"
        )

        assert success is False
        assert "insufficient stock" in error.lower()

    @patch('app.services.sales_management_service.get_db_session')
    def test_create_sale_invalid_payment_method(self, mock_get_db_session):
        """Test sale creation fails with invalid payment method."""
        success, error, sale_id = create_sale(
            customer_id=1,
            items=[],
            payment_method="invalid_method"
        )

        assert success is False
        assert error is not None


class TestCancelSale:
    """Tests for cancel_sale function."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_cancel_sale_success(self, mock_get_db_session):
        """Test successful sale cancellation with stock restoration."""
        # Mock sale with items
        mock_sale = Mock(
            id=1,
            status='completed',
            payment_method='cash',
            total=Decimal("100")
        )

        mock_item1 = Mock(product_id=1, quantity=2)
        mock_item2 = Mock(product_id=2, quantity=1)
        mock_sale.items = [mock_item1, mock_item2]

        # Mock products for stock restoration
        mock_product1 = Mock(stock=Decimal("10"))
        mock_product2 = Mock(stock=Decimal("5"))

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_sale,
            mock_product1,
            mock_product2
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = cancel_sale(1)

        assert success is True
        assert error is None
        assert mock_sale.status == 'cancelled'
        mock_db.commit.assert_called_once()

    @patch('app.services.sales_management_service.get_db_session')
    def test_cancel_sale_not_found(self, mock_get_db_session):
        """Test cancelling non-existent sale."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = cancel_sale(999)

        assert success is False
        assert "not found" in error.lower()

    @patch('app.services.sales_management_service.get_db_session')
    def test_cancel_already_cancelled_sale(self, mock_get_db_session):
        """Test cancelling an already cancelled sale."""
        mock_sale = Mock(id=1, status='cancelled')
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_sale
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = cancel_sale(1)

        assert success is False
        assert "already cancelled" in error.lower()


class TestAddPayment:
    """Tests for add_payment function."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_add_payment_success(self, mock_get_db_session):
        """Test successful payment addition."""
        mock_sale = Mock(
            id=1,
            total=Decimal("100"),
            status='completed',
            payment_method='credit'
        )
        mock_sale.payments = []
        mock_sale.customer = Mock(balance=Decimal("100"))

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_sale
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = add_payment(
            sale_id=1,
            amount=50,
            payment_method="cash"
        )

        assert success is True
        assert error is None
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    @patch('app.services.sales_management_service.get_db_session')
    def test_add_payment_exceeds_balance(self, mock_get_db_session):
        """Test payment fails when amount exceeds balance."""
        mock_sale = Mock(
            id=1,
            total=Decimal("100"),
            status='completed'
        )
        mock_sale.payments = [Mock(amount=Decimal("30"))]  # Already paid 30

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_sale
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = add_payment(
            sale_id=1,
            amount=100,  # Total is 100, already paid 30, remaining is 70
            payment_method="cash"
        )

        assert success is False
        assert "exceeds remaining balance" in error.lower()


class TestGetSalesSummary:
    """Tests for get_sales_summary function."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_get_sales_summary(self, mock_get_db_session):
        """Test getting sales summary for a period."""
        mock_sales = [
            Mock(total=Decimal("100"), discount_amount=Decimal("0"), tax_amount=Decimal("10")),
            Mock(total=Decimal("200"), discount_amount=Decimal("10"), tax_amount=Decimal("19")),
            Mock(total=Decimal("150"), discount_amount=Decimal("0"), tax_amount=Decimal("15"))
        ]

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_sales
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        from datetime import datetime
        summary = get_sales_summary(datetime.now(), datetime.now())

        assert summary['total_sales'] == 3
        assert summary['total_amount'] == 450.0
        assert summary['total_discount'] == 10.0
        assert summary['total_tax'] == 44.0
        assert summary['average_sale'] == 150.0


class TestValidatePositiveNumber:
    """Tests for validate_positive_number function."""

    def test_valid_positive_numbers(self):
        """Test validation of valid positive numbers."""
        assert validate_positive_number(1) == (True, None)
        assert validate_positive_number(0.01) == (True, None)
        assert validate_positive_number(1000) == (True, None)
        assert validate_positive_number("50.5") == (True, None)

    def test_zero_and_negative(self):
        """Test validation rejects zero and negative numbers."""
        result, error = validate_positive_number(0)
        assert result is False
        assert "greater than zero" in error.lower()

        result, error = validate_positive_number(-1)
        assert result is False
        assert "greater than zero" in error.lower()

    def test_invalid_values(self):
        """Test validation rejects non-numeric values."""
        result, error = validate_positive_number("abc")
        assert result is False
        assert "valid number" in error.lower()

        result, error = validate_positive_number(None)
        assert result is False
        assert "valid number" in error.lower()
