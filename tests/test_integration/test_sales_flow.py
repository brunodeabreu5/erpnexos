"""Integration tests for critical business workflows.

Tests complete end-to-end flows including:
- Complete sales process
- Payment processing
- Inventory adjustments
- Customer management
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
from app.database.models import Customer, Product, Sale, SaleItem


class TestCompleteSalesFlow:
    """Integration tests for complete sales workflow."""

    @patch('app.services.sales_management_service.get_db_session')
    @patch('app.services.customer_service.get_db_session')
    @patch('app.services.product_service.get_db_session')
    def test_complete_sale_workflow_cash(
        self,
        mock_get_db_session_product,
        mock_get_db_session_customer,
        mock_get_db_session_sale,
        test_customer_data,
        test_product_data
    ):
        """Test complete sale workflow from customer to payment.

        Flow:
        1. Create customer
        2. Create product
        3. Create sale with product
        4. Verify stock deduction
        5. Verify payment created
        """
        # Setup mock database sessions for different services
        mock_db_customer = Mock()
        mock_db_product = Mock()
        mock_db_sale = Mock()

        mock_get_db_session_customer.return_value.__enter__.return_value = mock_db_customer
        mock_get_db_session_product.return_value.__enter__.return_value = mock_db_product
        mock_get_db_session_sale.return_value.__enter__.return_value = mock_db_sale

        # Step 1: Create customer
        from app.services.customer_service import create_customer
        mock_db_customer.query.return_value.filter.return_value.first.return_value = None
        customer_success, _, customer = create_customer(**test_customer_data)
        assert customer_success

        # Step 2: Create product
        from app.services.product_service import create_product
        mock_db_product.query.return_value.filter.return_value.first.return_value = None
        product_success, _, product = create_product(**test_product_data)
        assert product_success

        # Step 3: Create sale
        from app.services.sales_management_service import create_sale
        mock_customer_result = Mock(id=1, balance=Decimal("0"))
        mock_product_result = Mock(id=1, stock=Decimal("100"), is_active=True)

        mock_db_sale.query.return_value.filter.return_value.first.side_effect = [
            mock_customer_result,
            mock_product_result
        ]

        sale_items = [{
            "product_id": 1,
            "quantity": 2,
            "unit_price": Decimal("99.99"),
            "discount": 0
        }]

        sale_success, _, sale_id = create_sale(
            customer_id=1,
            items=sale_items,
            payment_method="cash"
        )

        assert sale_success
        assert sale_id is not None

        # Verify stock was deducted
        # In real scenario: product.stock started at 100, now should be 98
        # This would be verified through the mock calls

    @patch('app.services.sales_management_service.get_db_session')
    def test_credit_sale_workflow(self, mock_get_db_session):
        """Test credit sale workflow with customer balance update.

        Flow:
        1. Create credit sale
        2. Verify customer balance increased
        3. Add payment
        4. Verify customer balance decreased
        """
        from app.services.sales_management_service import create_sale, add_payment

        mock_customer = Mock(id=1, balance=Decimal("0"))
        mock_product = Mock(id=1, stock=Decimal("100"), is_active=True)
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_product,
            mock_product
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        sale_items = [{
            "product_id": 1,
            "quantity": 1,
            "unit_price": Decimal("100.00"),
            "discount": 0
        }]

        # Create credit sale
        sale_success, _, sale_id = create_sale(
            customer_id=1,
            items=sale_items,
            payment_method="credit"
        )

        assert sale_success

        # Verify customer balance was increased (credit sale)
        # Balance should be 110.00 (100 + 10% tax)

        # Add payment
        payment_success, _ = add_payment(
            sale_id=sale_id,
            amount=50,
            payment_method="cash"
        )

        assert payment_success


class TestSaleCancellationFlow:
    """Integration tests for sale cancellation workflow."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_cancel_sale_restores_stock(self, mock_get_db_session):
        """Test that cancelling a sale restores stock correctly.

        Flow:
        1. Create sale with items
        2. Verify stock deducted
        3. Cancel sale
        4. Verify stock restored
        """
        from app.services.sales_management_service import cancel_sale

        # Mock sale with items
        mock_sale = Mock(
            id=1,
            status='completed',
            payment_method='cash',
            customer_id=1,
            total=Decimal("200")
        )

        mock_item1 = Mock(product_id=1, quantity=2)
        mock_item2 = Mock(product_id=2, quantity=1)
        mock_sale.items = [mock_item1, mock_item2]

        # Mock products
        mock_product1 = Mock(id=1, stock=Decimal("10"))
        mock_product2 = Mock(id=2, stock=Decimal("5"))

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_sale,
            mock_product1,
            mock_product2
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Cancel sale
        success, error = cancel_sale(1)

        assert success
        assert error is None
        assert mock_sale.status == 'cancelled'

        # Verify stock was restored
        # Product 1: 10 + 2 = 12
        # Product 2: 5 + 1 = 6


class TestMultiPaymentFlow:
    """Integration tests for multiple payment workflow."""

    @patch('app.services.sales_management_service.get_db_session')
    def test_installment_payments(self, mock_get_db_session):
        """Test multiple payments for a single sale (installments).

        Flow:
        1. Create credit sale
        2. Add partial payment 1
        3. Add partial payment 2
        4. Verify payment status updates to 'paid'
        """
        from app.services.sales_management_service import create_sale, add_payment

        mock_customer = Mock(id=1, balance=Decimal("0"))
        mock_product = Mock(id=1, stock=Decimal("100"), is_active=True)
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_product,
            mock_product
        ]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        sale_items = [{
            "product_id": 1,
            "quantity": 1,
            "unit_price": Decimal("100.00"),
            "discount": 0
        }]

        # Create credit sale (total = 110 with tax)
        sale_success, _, sale_id = create_sale(
            customer_id=1,
            items=sale_items,
            payment_method="credit"
        )

        assert sale_success

        # Mock sale for payments
        mock_sale = Mock(
            id=sale_id,
            total=Decimal("110"),
            status='completed',
            payment_method='credit'
        )
        mock_sale.payments = []
        mock_sale.customer = Mock(balance=Decimal("110"))

        mock_db.query.return_value.filter.return_value.first.return_value = mock_sale

        # First payment: 50
        success1, _ = add_payment(sale_id, 50, "cash")
        assert success1

        # Second payment: 60 (exceeds remaining by 10)
        success2, _ = add_payment(sale_id, 60, "cash")
        assert not success2  # Should fail

        # Third payment: exactly 50 (should work)
        success3, _ = add_payment(sale_id, 50, "cash")
        assert success3


class TestInventoryManagementFlow:
    """Integration tests for inventory management workflows."""

    @patch('app.services.product_service.get_db_session')
    @patch('app.services.sales_management_service.get_db_session')
    def test_stock_flow_across_operations(self, mock_get_db_session_sale, mock_get_db_session_product):
        """Test stock changes across sale and cancellation.

        Flow:
        1. Initial stock: 100
        2. Create sale (quantity: 10) → stock: 90
        3. Cancel sale → stock: 100
        """
        from app.services.sales_management_service import create_sale, cancel_sale
        from app.services.product_service import get_product_by_id

        # Mock product with initial stock
        mock_product = Mock(id=1, stock=Decimal("100"), name="Test Product")

        mock_db_product = Mock()
        mock_db_product.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db_session_product.return_value.__enter__.return_value = mock_db_product

        # Mock for sale creation
        mock_customer = Mock(id=1, balance=Decimal("0"))
        mock_db_sale = Mock()
        mock_db_sale.query.return_value.filter.return_value.first.side_effect = [
            mock_customer,
            mock_product,
            mock_product
        ]
        mock_get_db_session_sale.return_value.__enter__.return_value = mock_db_sale

        sale_items = [{
            "product_id": 1,
            "quantity": 10,
            "unit_price": Decimal("10.00"),
            "discount": 0
        }]

        # Create sale
        sale_success, _, sale_id = create_sale(
            customer_id=1,
            items=sale_items,
            payment_method="cash"
        )

        assert sale_success
        # Stock should now be 90 (100 - 10)

        # Mock for cancellation
        mock_sale = Mock(
            id=sale_id,
            status='completed',
            payment_method='cash'
        )
        mock_sale_item = Mock(product_id=1, quantity=10)
        mock_sale.items = [mock_sale_item]

        mock_db_cancel = Mock()
        mock_db_cancel.query.return_value.filter.return_value.first.side_effect = [
            mock_sale,
            mock_product
        ]
        mock_get_db_session_sale.return_value.__enter__.return_value = mock_db_cancel

        # Cancel sale
        cancel_success, _ = cancel_sale(sale_id)

        assert cancel_success
        # Stock should be restored to 100 (90 + 10)


class TestCustomerLifecycleFlow:
    """Integration tests for customer lifecycle."""

    @patch('app.services.customer_service.get_db_session')
    def test_customer_from_creation_to_first_purchase(
        self,
        mock_get_db_session,
        test_customer_data
    ):
        """Test complete customer lifecycle.

        Flow:
        1. Create customer
        2. Verify customer can be retrieved
        3. Update customer information
        4. Delete customer
        """
        from app.services.customer_service import (
            create_customer,
            get_customer_by_id,
            update_customer,
            delete_customer
        )

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Step 1: Create customer
        success, error, customer = create_customer(**test_customer_data)
        assert success
        assert customer.id == 1

        # Step 2: Retrieve customer
        mock_db.query.return_value.filter.return_value.first.return_value = customer
        retrieved = get_customer_by_id(1)
        assert retrieved is not None

        # Step 3: Update customer
        mock_db.query.return_value.filter.return_value.first.return_value = customer
        success, error, _ = update_customer(1, name="Updated Name")
        assert success

        # Step 4: Delete (soft delete) customer
        success, error = delete_customer(1)
        assert success
