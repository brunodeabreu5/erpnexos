"""Unit tests for the authentication service.

Tests user authentication, password hashing/verification, and admin user creation.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.auth_service import (
    authenticate_user,
    create_admin_user,
    change_password,
)
from app.database.models import User


class TestAuthenticateUser:
    """Tests for authenticate_user function."""

    @patch('app.services.auth_service.get_db_session')
    def test_successful_authentication(self, mock_get_db_session):
        """Test successful authentication with valid credentials."""
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.username = "admin"
        mock_user.is_active = True
        mock_user.hashed_password = User.hash_password("admin123")

        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # Test authentication
        success, error = authenticate_user("admin", "admin123")

        assert success is True
        assert error is None

    @patch('app.services.auth_service.get_db_session')
    def test_user_not_found(self, mock_get_db_session):
        """Test authentication fails when user doesn't exist."""
        # Mock database session returning None
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = authenticate_user("nonexistent", "password")

        assert success is False
        assert "Invalid username or password" in error

    @patch('app.services.auth_service.get_db_session')
    def test_wrong_password(self, mock_get_db_session):
        """Test authentication fails with wrong password."""
        mock_user = Mock(spec=User)
        mock_user.username = "admin"
        mock_user.is_active = True
        mock_user.hashed_password = User.hash_password("correctpassword")

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = authenticate_user("admin", "wrongpassword")

        assert success is False
        assert "Invalid username or password" in error

    @patch('app.services.auth_service.get_db_session')
    def test_inactive_user(self, mock_get_db_session):
        """Test authentication fails for inactive user."""
        mock_user = Mock(spec=User)
        mock_user.username = "admin"
        mock_user.is_active = False
        mock_user.hashed_password = User.hash_password("password")

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = authenticate_user("admin", "password")

        assert success is False
        assert "disabled" in error.lower()

    def test_empty_credentials(self):
        """Test authentication fails with empty username or password."""
        success, error = authenticate_user("", "password")
        assert success is False
        assert "required" in error.lower()

        success, error = authenticate_user("admin", "")
        assert success is False
        assert "required" in error.lower()

        success, error = authenticate_user("", "")
        assert success is False
        assert "required" in error.lower()

    @patch('app.services.auth_service.get_db_session')
    def test_database_error(self, mock_get_db_session):
        """Test authentication handles database errors gracefully."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection error")
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = authenticate_user("admin", "password")

        assert success is False
        assert "error" in error.lower()


class TestCreateAdminUser:
    """Tests for create_admin_user function."""

    @patch('app.services.auth_service.get_db_session')
    def test_create_new_admin_user(self, mock_get_db_session):
        """Test creating a new admin user."""
        # Mock user not found (doesn't exist yet)
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = create_admin_user("newadmin", "password123")

        assert success is True
        assert error is None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.services.auth_service.get_db_session')
    def test_admin_user_already_exists(self, mock_get_db_session):
        """Test when admin user already exists."""
        # Mock existing user
        mock_user = Mock(spec=User)
        mock_user.username = "admin"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = create_admin_user("admin", "password123")

        assert success is True
        assert error is None
        # Should not add a new user
        mock_db.add.assert_not_called()

    @patch('app.services.auth_service.get_db_session')
    def test_database_error_on_create(self, mock_get_db_session):
        """Test handling database errors during admin creation."""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = create_admin_user("admin", "password123")

        assert success is False
        assert error is not None
        assert "database error" in error.lower()


class TestChangePassword:
    """Tests for change_password function."""

    @patch('app.services.auth_service.get_db_session')
    def test_successful_password_change(self, mock_get_db_session):
        """Test successful password change."""
        mock_user = Mock(spec=User)
        mock_user.username = "admin"
        mock_user.hashed_password = User.hash_password("oldpassword")

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = change_password("admin", "oldpassword", "newpassword123")

        assert success is True
        assert error is None
        assert mock_user.hashed_password != User.hash_password("oldpassword")

    @patch('app.services.auth_service.get_db_session')
    def test_user_not_found(self, mock_get_db_session):
        """Test password change fails for non-existent user."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = change_password("nonexistent", "oldpass", "newpass")

        assert success is False
        assert "not found" in error.lower()

    @patch('app.services.auth_service.get_db_session')
    def test_wrong_old_password(self, mock_get_db_session):
        """Test password change fails with wrong old password."""
        mock_user = Mock(spec=User)
        mock_user.username = "admin"
        mock_user.hashed_password = User.hash_password("correctold")

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        success, error = change_password("admin", "wrongold", "newpass")

        assert success is False
        assert "incorrect" in error.lower()

    def test_password_too_short(self):
        """Test password change fails when new password is too short."""
        success, error = change_password("admin", "oldpass", "short")

        assert success is False
        assert "at least 6 characters" in error.lower()


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_hash(self):
        """Test that hash_password returns a hashed string."""
        password = "testpassword123"
        hashed = User.hash_password(password)

        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # Bcrypt hash prefix

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = User.hash_password(password)

        assert User.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = User.hash_password(password)

        assert User.verify_password(wrong_password, hashed) is False

    def test_hash_is_unique(self):
        """Test that hashing the same password twice produces different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = User.hash_password(password)
        hash2 = User.hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert User.verify_password(password, hash1) is True
        assert User.verify_password(password, hash2) is True
