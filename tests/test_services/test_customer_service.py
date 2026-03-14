"""Unit tests for the customer service module.

Tests customer CRUD operations, validation, and business logic.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from app.services.customer_service import (
    create_customer,
    list_customers,
    get_customer_by_id,
    update_customer,
    delete_customer,
    search_customers
)
from app.database.models import Customer
from app.types import Result


class TestCreateCustomer:
    """Tests for create_customer function."""

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_success(self, mock_get_db_session, test_customer_data):
        """Test successful customer creation."""
        # Setup mock
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No duplicates
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Execute
        result = create_customer(**test_customer_data)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 3
        success, error, customer = result
        assert success is True
        assert error is None
        assert customer is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_duplicate_email(self, mock_get_db_session, test_customer_data):
        """Test customer creation fails with duplicate email."""
        # Setup mock - existing customer with same email
        mock_existing = Mock()
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Execute
        result = create_customer(**test_customer_data)

        # Assert
        success, error, customer = result
        assert success is False
        assert "already registered" in error.lower()
        assert customer is None

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_duplicate_tax_id(self, mock_get_db_session, test_customer_data):
        """Test customer creation fails with duplicate tax ID."""
        # Setup mock - first check email (ok), second check tax_id (duplicate)
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, Mock()]
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Execute
        result = create_customer(**test_customer_data)

        # Assert
        success, error, customer = result
        assert success is False
        assert "tax id already registered" in error.lower()

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_invalid_name(self, mock_get_db_session):
        """Test customer creation fails with invalid name."""
        mock_db = Mock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = create_customer(name="")  # Empty name

        assert result[0] is False
        assert "required" in result[1].lower()

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_invalid_email(self, mock_get_db_session):
        """Test customer creation fails with invalid email."""
        mock_db = Mock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = create_customer(name="Test", email="invalid-email")

        assert result[0] is False
        assert "invalid" in result[1].lower()

    @patch('app.services.customer_service.get_db_session')
    def test_create_customer_database_error(self, mock_get_db_session, test_customer_data):
        """Test customer creation handles database errors."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = create_customer(**test_customer_data)

        assert result[0] is False
        assert "error" in result[1].lower()


class TestListCustomers:
    """Tests for list_customers function."""

    @patch('app.services.customer_service.get_db_session')
    def test_list_all_customers(self, mock_get_db_session):
        """Test listing all customers."""
        # Setup mock customers
        mock_customers = [
            Mock(id=1, name="Customer A", is_active=True),
            Mock(id=2, name="Customer B", is_active=True),
            Mock(id=3, name="Customer C", is_active=True)
        ]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_customers
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Execute
        result = list_customers(active_only=False)

        # Assert
        assert len(result) == 3
        assert result == mock_customers

    @patch('app.services.customer_service.get_db_session')
    def test_list_active_customers_only(self, mock_get_db_session):
        """Test listing only active customers."""
        mock_customers = [Mock(id=1, name="Active Customer", is_active=True)]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_customers
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = list_customers(active_only=True)

        assert len(result) == 1
        mock_query.filter.assert_called_once()

    @patch('app.services.customer_service.get_db_session')
    def test_list_customers_empty(self, mock_get_db_session):
        """Test listing customers when none exist."""
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = list_customers()

        assert result == []


class TestGetCustomerById:
    """Tests for get_customer_by_id function."""

    @patch('app.services.customer_service.get_db_session')
    def test_get_existing_customer(self, mock_get_db_session, mock_customer):
        """Test retrieving an existing customer by ID."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = get_customer_by_id(1)

        assert result is not None
        assert result.id == 1

    @patch('app.services.customer_service.get_db_session')
    def test_get_nonexistent_customer(self, mock_get_db_session):
        """Test retrieving a non-existent customer returns None."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = get_customer_by_id(999)

        assert result is None


class TestUpdateCustomer:
    """Tests for update_customer function."""

    @patch('app.services.customer_service.get_db_session')
    def test_update_customer_success(self, mock_get_db_session):
        """Test successful customer update."""
        mock_customer = Mock()
        mock_customer.id = 1
        mock_customer.name = "Old Name"
        mock_customer.email = "old@example.com"
        mock_customer.is_active = True

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = update_customer(1, name="New Name", email="new@example.com")

        assert result[0] is True
        assert result[1] is None
        assert result[2].id == 1
        mock_db.commit.assert_called_once()

    @patch('app.services.customer_service.get_db_session')
    def test_update_customer_not_found(self, mock_get_db_session):
        """Test updating non-existent customer fails."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = update_customer(999, name="New Name")

        assert result[0] is False
        assert "not found" in result[1].lower()


class TestDeleteCustomer:
    """Tests for delete_customer function."""

    @patch('app.services.customer_service.get_db_session')
    def test_delete_customer_success(self, mock_get_db_session):
        """Test successful customer deletion (soft delete)."""
        mock_customer = Mock()
        mock_customer.id = 1
        mock_customer.is_active = True

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = delete_customer(1)

        assert result[0] is True
        assert result[1] is None
        mock_db.commit.assert_called_once()

    @patch('app.services.customer_service.get_db_session')
    def test_delete_customer_not_found(self, mock_get_db_session):
        """Test deleting non-existent customer fails."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = delete_customer(999)

        assert result[0] is False
        assert "not found" in result[1].lower()


class TestSearchCustomers:
    """Tests for search_customers function."""

    @patch('app.services.customer_service.get_db_session')
    def test_search_by_name(self, mock_get_db_session):
        """Test searching customers by name."""
        mock_results = [
            Mock(id=1, name="John Doe", is_active=True),
            Mock(id=2, name="Jane Smith", is_active=True)
        ]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = search_customers("John")

        assert len(result) == 1
        assert result[0].id == 1

    @patch('app.services.customer_service.get_db_session')
    def test_search_by_email(self, mock_get_db_session):
        """Test searching customers by email."""
        mock_results = [Mock(id=1, email="test@example.com", is_active=True)]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = search_customers("test@example.com")

        assert len(result) == 1

    @patch('app.services.customer_service.get_db_session')
    def test_search_empty_results(self, mock_get_db_session):
        """Test search returns no results."""
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = search_customers("NonExistent")

        assert result == []
