"""Unit tests for the supplier service module.

Tests supplier CRUD operations, validation, and business logic.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.supplier_service import (
    create_supplier,
    list_suppliers,
    get_supplier_by_id,
    update_supplier,
    delete_supplier,
    search_suppliers
)


class TestCreateSupplier:
    """Tests for create_supplier function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_create_supplier_success(self, mock_get_db_session, test_supplier_data):
        """Test successful supplier creation."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, supplier = create_supplier(**test_supplier_data)

        assert success is True
        assert error is None
        assert supplier is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.services.supplier_service.get_db_session')
    def test_create_supplier_duplicate_tax_id(self, mock_get_db_session, test_supplier_data):
        """Test supplier creation fails with duplicate tax ID."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, supplier = create_supplier(**test_supplier_data)

        assert success is False
        assert "tax id already registered" in error.lower()
        assert supplier is None

    @patch('app.services.supplier_service.get_db_session')
    def test_create_supplier_invalid_name(self, mock_get_db_session):
        """Test supplier creation fails with invalid name."""
        mock_db = Mock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, supplier = create_supplier(name="")

        assert success is False
        assert "required" in error.lower()

    @patch('app.services.supplier_service.get_db_session')
    def test_create_supplier_invalid_email(self, mock_get_db_session, test_supplier_data):
        """Test supplier creation fails with invalid email."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        test_data = test_supplier_data.copy()
        test_data['email'] = 'invalid-email'

        success, error, supplier = create_supplier(**test_data)

        assert success is False
        assert "invalid" in error.lower()


class TestListSuppliers:
    """Tests for list_suppliers function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_list_all_suppliers(self, mock_get_db_session):
        """Test listing all suppliers."""
        mock_suppliers = [
            Mock(id=1, name="Supplier A", is_active=True),
            Mock(id=2, name="Supplier B", is_active=True)
        ]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_suppliers
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = list_suppliers(active_only=False)

        assert len(result) == 2

    @patch('app.services.supplier_service.get_db_session')
    def test_list_active_suppliers_only(self, mock_get_db_session):
        """Test listing only active suppliers."""
        mock_suppliers = [Mock(id=1, name="Active Supplier", is_active=True)]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_suppliers
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = list_suppliers(active_only=True)

        assert len(result) == 1


class TestGetSupplierById:
    """Tests for get_supplier_by_id function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_get_existing_supplier(self, mock_get_db_session):
        """Test retrieving an existing supplier."""
        mock_supplier = Mock(id=1, name="Test Supplier")
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = get_supplier_by_id(1)

        assert result is not None
        assert result.id == 1

    @patch('app.services.supplier_service.get_db_session')
    def test_get_nonexistent_supplier(self, mock_get_db_session):
        """Test retrieving non-existent supplier returns None."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = get_supplier_by_id(999)

        assert result is None


class TestUpdateSupplier:
    """Tests for update_supplier function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_update_supplier_success(self, mock_get_db_session):
        """Test successful supplier update."""
        mock_supplier = Mock(id=1, name="Old Name")
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, supplier = update_supplier(1, name="New Name")

        assert success is True
        assert error is None
        mock_db.commit.assert_called_once()

    @patch('app.services.supplier_service.get_db_session')
    def test_update_supplier_not_found(self, mock_get_db_session):
        """Test updating non-existent supplier fails."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error, supplier = update_supplier(999, name="New Name")

        assert success is False
        assert "not found" in error.lower()


class TestDeleteSupplier:
    """Tests for delete_supplier function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_delete_supplier_success(self, mock_get_db_session):
        """Test successful supplier deletion."""
        mock_supplier = Mock(id=1, is_active=True)
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = delete_supplier(1)

        assert success is True
        assert error is None
        mock_db.commit.assert_called_once()

    @patch('app.services.supplier_service.get_db_session')
    def test_delete_supplier_not_found(self, mock_get_db_session):
        """Test deleting non-existent supplier fails."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = delete_supplier(999)

        assert success is False
        assert "not found" in error.lower()


class TestSearchSuppliers:
    """Tests for search_suppliers function."""

    @patch('app.services.supplier_service.get_db_session')
    def test_search_by_name(self, mock_get_db_session):
        """Test searching suppliers by name."""
        mock_results = [Mock(id=1, name="Test Supplier", is_active=True)]
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = search_suppliers("Test")

        assert len(result) == 1

    @patch('app.services.supplier_service.get_db_session')
    def test_search_empty_results(self, mock_get_db_session):
        """Test search returns no results."""
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        result = search_suppliers("NonExistent")

        assert result == []
