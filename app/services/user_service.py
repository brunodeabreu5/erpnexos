"""User service module for ERP Paraguay.

This module provides business logic for user management operations.
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from app.database.db import get_db_session
from app.database.models import User, AuditLog
from app.database.models import User
from app.validators import (
    validate_username,
    validate_password,
    validate_email,
    validate_required_string
)

logger = logging.getLogger(__name__)

# Valid roles
VALID_ROLES = ['admin', 'manager', 'sales', 'viewer']


def create_user(
    username: str,
    password: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role: str = 'sales'
) -> Tuple[bool, Optional[str], Optional[User]]:
    """Create a new user in the database.

    Args:
        username: Unique username (required)
        password: User password (required)
        full_name: User's full name (optional)
        email: User email (optional, must be unique)
        role: User role (default: 'sales')

    Returns:
        Tuple of (success: bool, error_message: Optional[str], user: Optional[User])
    """
    # Validate username
    is_valid, error = validate_username(username)
    if not is_valid:
        return False, error, None

    # Validate password
    is_valid, error = validate_password(password)
    if not is_valid:
        return False, error, None

    # Validate email if provided
    if email:
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, error, None

    # Validate role
    if role not in VALID_ROLES:
        return False, f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}", None

    try:
        with get_db_session() as db:
            # Check for duplicate username
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                return False, "Username already exists", None

            # Check for duplicate email
            if email:
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    return False, "Email already registered", None

            # Create user
            user = User(
                username=username.strip(),
                hashed_password=User.hash_password(password),
                full_name=full_name.strip() if full_name else None,
                email=email.strip() if email else None,
                role=role,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created user: {user}")
            return True, None, user

    except Exception as e:
        logger.error(f"Failed to create user '{username}': {e}", exc_info=True)
        return False, "An error occurred while creating user", None


def list_users(include_inactive: bool = False) -> List[User]:
    """Retrieve all users from the database.

    Args:
        include_inactive: If True, include inactive users

    Returns:
        List of User objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(User)
            if not include_inactive:
                query = query.filter(User.is_active == True)
            users = query.order_by(User.username).all()
            logger.info(f"Retrieved {len(users)} users")
            return users
    except Exception as e:
        logger.error(f"Failed to retrieve users: {e}", exc_info=True)
        raise


def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve a single user by its ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        User object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                logger.info(f"Retrieved user ID {user_id}")
            else:
                logger.warning(f"User ID {user_id} not found")
            return user
    except Exception as e:
        logger.error(f"Failed to retrieve user ID {user_id}: {e}", exc_info=True)
        raise


def get_user_by_username(username: str) -> Optional[User]:
    """Retrieve a single user by username.

    Args:
        username: The username to search for

    Returns:
        User object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return user
    except Exception as e:
        logger.error(f"Failed to retrieve user '{username}': {e}", exc_info=True)
        raise


def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[bool, Optional[str], Optional[User]]:
    """Update an existing user.

    Args:
        user_id: ID of the user to update
        full_name: New full name (optional)
        email: New email (optional)
        role: New role (optional)
        is_active: New active status (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], user: Optional[User])
    """
    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, f"User ID {user_id} not found", None

            # Validate and update full_name if provided
            if full_name is not None:
                user.full_name = full_name.strip() if full_name else None

            # Validate and update email if provided
            if email is not None:
                if email:  # Non-empty email
                    is_valid, error = validate_email(email)
                    if not is_valid:
                        return False, error, None
                    # Check for duplicate email
                    existing = db.query(User).filter(
                        User.email == email,
                        User.id != user_id
                    ).first()
                    if existing:
                        return False, "Email already registered", None
                    user.email = email.strip()
                else:  # Empty string, set to None
                    user.email = None

            # Validate and update role if provided
            if role is not None:
                if role not in VALID_ROLES:
                    return False, f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}", None
                user.role = role

            # Update is_active if provided
            if is_active is not None:
                user.is_active = is_active

            db.commit()
            db.refresh(user)
            logger.info(f"Updated user ID {user_id}: {user}")
            return True, None, user

    except Exception as e:
        logger.error(f"Failed to update user ID {user_id}: {e}", exc_info=True)
        return False, "An error occurred while updating user", None


def change_user_password(user_id: int, new_password: str) -> Tuple[bool, Optional[str]]:
    """Change a user's password.

    Args:
        user_id: ID of the user
        new_password: New password

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    # Validate password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        return False, error

    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, f"User ID {user_id} not found"

            user.hashed_password = User.hash_password(new_password)
            db.commit()
            logger.info(f"Password changed for user ID {user_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to change password for user ID {user_id}: {e}", exc_info=True)
        return False, "An error occurred while changing password"


def deactivate_user(user_id: int) -> Tuple[bool, Optional[str]]:
    """Deactivate a user account.

    Args:
        user_id: ID of the user to deactivate

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, f"User ID {user_id} not found"

            user.is_active = False
            db.commit()
            logger.info(f"Deactivated user ID {user_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to deactivate user ID {user_id}: {e}", exc_info=True)
        return False, "An error occurred while deactivating user"


def create_audit_log(
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
) -> bool:
    """Create an audit log entry.

    Args:
        user_id: ID of the user performing the action
        action: Action performed (create_sale, delete_product, etc.)
        entity_type: Type of entity (Sale, Product, Customer, etc.)
        entity_id: ID of the affected entity
        old_values: Previous values (for updates/deletes)
        new_values: New values (for creates/updates)

    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_session() as db:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values
            )
            db.add(audit_log)
            db.commit()
            logger.info(f"Created audit log: user_id={user_id}, action={action}, entity_type={entity_type}, entity_id={entity_id}")
            return True

    except Exception as e:
        logger.error(f"Failed to create audit log: {e}", exc_info=True)
        return False


def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    limit: int = 100
) -> List[AuditLog]:
    """Retrieve audit logs with optional filters.

    Args:
        user_id: Filter by user ID (optional)
        action: Filter by action (optional)
        entity_type: Filter by entity type (optional)
        entity_id: Filter by entity ID (optional)
        limit: Maximum number of logs to return

    Returns:
        List of AuditLog objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(AuditLog)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if entity_type:
                query = query.filter(AuditLog.entity_type == entity_type)
            if entity_id:
                query = query.filter(AuditLog.entity_id == entity_id)

            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
            return logs

    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}", exc_info=True)
        raise
