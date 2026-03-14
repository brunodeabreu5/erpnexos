
import logging
from typing import Tuple, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.db import get_db_session
from app.database.models import User, AuditLog
from app.config import (
    MIN_PASSWORD_LENGTH,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    MAX_LOGIN_ATTEMPTS,
    LOGIN_BLOCK_MINUTES,
    set_request_context,
    clear_request_context,
    generate_request_id
)

logger = logging.getLogger(__name__)


# Store failed login attempts: {username: [(timestamp, success)]}
_login_attempts = {}


def _is_login_blocked(username: str) -> bool:
    """Check if a username is temporarily blocked due to too many failed attempts.

    Args:
        username: The username to check

    Returns:
        True if blocked, False otherwise
    """
    if username not in _login_attempts:
        return False

    # Get recent failed attempts (within block window)
    now = datetime.now()
    block_window = now - timedelta(minutes=LOGIN_BLOCK_MINUTES)
    recent_failures = [
        ts for ts, success in _login_attempts[username]
        if ts > block_window and not success
    ]

    # Check if max attempts exceeded
    if len(recent_failures) >= MAX_LOGIN_ATTEMPTS:
        return True

    return False


def _record_login_attempt(username: str, success: bool) -> None:
    """Record a login attempt for rate limiting.

    Args:
        username: The username attempting to log in
        success: Whether the attempt was successful
    """
    if username not in _login_attempts:
        _login_attempts[username] = []

    # Clean old attempts outside block window
    now = datetime.now()
    block_window = now - timedelta(minutes=LOGIN_BLOCK_MINUTES)
    _login_attempts[username] = [
        (ts, succ) for ts, succ in _login_attempts[username]
        if ts > block_window
    ]

    # Add current attempt (keep last MAX_LOGIN_ATTEMPTS + 1 for accurate tracking)
    _login_attempts[username].append((now, success))
    if len(_login_attempts[username]) > MAX_LOGIN_ATTEMPTS + 1:
        _login_attempts[username] = _login_attempts[username][-(MAX_LOGIN_ATTEMPTS + 1):]


def _get_remaining_block_time(username: str) -> Optional[int]:
    """Get remaining minutes until block expires.

    Args:
        username: The username to check

    Returns:
        Remaining minutes if blocked, None otherwise
    """
    if username not in _login_attempts:
        return None

    now = datetime.now()
    block_window = now - timedelta(minutes=LOGIN_BLOCK_MINUTES)
    recent_failures = [
        ts for ts, success in _login_attempts[username]
        if ts > block_window and not success
    ]

    if len(recent_failures) >= MAX_LOGIN_ATTEMPTS:
        # Find when the block will expire (oldest recent failure + block minutes)
        oldest_failure = min(recent_failures)
        expiry_time = oldest_failure + timedelta(minutes=LOGIN_BLOCK_MINUTES)
        remaining_minutes = int((expiry_time - now).total_seconds() / 60) + 1
        return remaining_minutes

    return None


def create_admin_user() -> Tuple[bool, Optional[str]]:
    """Create the initial admin user if it doesn't exist.

    This function should be called during database initialization to ensure
    at least one admin user exists in the system. The admin credentials are
    loaded from environment variables ADMIN_USERNAME and ADMIN_PASSWORD.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
        - (True, None) if user created or already exists
        - (False, error_message) if creation failed
    """
    # Validate admin password is configured
    if not ADMIN_PASSWORD:
        error_msg = "ADMIN_PASSWORD environment variable not set. Please configure in .env file"
        logger.error(error_msg)
        return False, error_msg

    try:
        with get_db_session() as db:
            # Check if admin user already exists
            existing_user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
            if existing_user:
                logger.info(f"Admin user '{ADMIN_USERNAME}' already exists")
                return True, None

            # Create new admin user with role
            hashed_password = User.hash_password(ADMIN_PASSWORD)
            admin_user = User(
                username=ADMIN_USERNAME,
                hashed_password=hashed_password,
                role='admin',
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Created admin user '{ADMIN_USERNAME}' with role 'admin'")
            return True, None

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}", exc_info=True)
        return False, f"Database error: {str(e)}"


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[dict]]:
    """Authenticate a user with username and password.

    Queries the database for the user and verifies the password using bcrypt.
    Implements rate limiting to prevent brute force attacks.
    Logs all authentication attempts for security auditing with structured context.

    Args:
        username: The username to authenticate
        password: The plain text password to verify

    Returns:
        Tuple of (success: bool, error_message: Optional[str], user_info: Optional[dict])
        - (True, None, user_info) if authentication successful
        - (False, error_message, None) if authentication failed
          Error messages are user-friendly and don't leak sensitive info
    """
    # Generate request ID for tracking this authentication attempt
    request_id = generate_request_id()
    set_request_context(username=username, request_id=request_id, action='authenticate')

    try:
        if not username or not password:
            logger.warning("Authentication failed: empty username or password")
            clear_request_context()
            return False, "Username and password are required", None

        # Check if user is blocked due to too many failed attempts
        if _is_login_blocked(username):
            remaining_minutes = _get_remaining_block_time(username)
            logger.warning(
                f"Authentication blocked for user '{username}': too many failed attempts",
                extra={'remaining_minutes': remaining_minutes, 'blocked': True}
            )
            clear_request_context()
            return False, f"Account temporarily blocked due to too many failed attempts. Try again in {remaining_minutes} minutes.", None

        with get_db_session() as db:
            # Query user by username
            user = db.query(User).filter(User.username == username).first()

            if not user:
                _record_login_attempt(username, False)
                logger.warning(f"Authentication failed: user '{username}' not found")
                clear_request_context()
                return False, "Invalid username or password", None

            if not user.is_active:
                _record_login_attempt(username, False)
                logger.warning(f"Authentication failed: user '{username}' is inactive", extra={'user_id': user.id})
                clear_request_context()
                return False, "Account is disabled", None

            # Verify password
            if not User.verify_password(password, user.hashed_password):
                _record_login_attempt(username, False)
                logger.warning(
                    f"Authentication failed: invalid password for user '{username}'",
                    extra={'user_id': user.id}
                )
                clear_request_context()
                return False, "Invalid username or password", None

            # Record successful login (clears failed attempts)
            _record_login_attempt(username, True)

            # Update context with user info
            set_request_context(user_id=user.id, username=username, request_id=request_id, action='authenticate')

            # Update last login
            user.last_login = datetime.now()
            db.commit()

            # Log to audit trail
            try:
                audit_log = AuditLog(
                    user_id=user.id,
                    action='LOGIN_SUCCESS',
                    entity_type='User',
                    entity_id=user.id,
                    new_values={'username': username, 'login_time': datetime.now().isoformat()}
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                # Don't fail login if audit logging fails
                logger.warning(f"Failed to log audit trail for login: {e}", exc_info=True)

            # Create user info dict (without sensitive data)
            user_info = {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role
            }

            logger.info(
                f"User '{username}' authenticated successfully",
                extra={'user_id': user.id, 'role': user.role}
            )
            clear_request_context()
            return True, None, user_info

    except Exception as e:
        logger.error(
            f"Authentication error for user '{username}'",
            exc_info=True,
            extra={'error_type': type(e).__name__}
        )
        clear_request_context()
        return False, "An error occurred during authentication", None


def update_last_login(username: str) -> bool:
    """Update the last login timestamp for a user.

    Args:
        username: The username to update

    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.last_login = datetime.now()
                db.commit()
                logger.info(f"Updated last login for user '{username}'")
                return True
            return False
    except Exception as e:
        logger.error(f"Failed to update last login for user '{username}': {e}", exc_info=True)
        return False


def change_password(
    username: str,
    old_password: str,
    new_password: str
) -> Tuple[bool, Optional[str]]:
    """Change a user's password after verifying the old password.

    Args:
        username: The username whose password to change
        old_password: Current password for verification
        new_password: New password to set

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    try:
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()

            if not user:
                return False, "User not found"

            if not User.verify_password(old_password, user.hashed_password):
                return False, "Current password is incorrect"

            # Set new password
            user.hashed_password = User.hash_password(new_password)
            db.commit()
            logger.info(f"Password changed successfully for user '{username}'")
            return True, None

    except Exception as e:
        logger.error(f"Password change error for user '{username}': {e}", exc_info=True)
        return False, "An error occurred while changing password"


# Permission matrix for role-based access control
PERMISSIONS = {
    'admin': {
        # Can do everything
        'create_sale', 'view_sale', 'cancel_sale', 'add_payment',
        'create_product', 'view_product', 'edit_product', 'delete_product',
        'create_customer', 'view_customer', 'edit_customer', 'delete_customer',
        'create_category', 'view_category', 'edit_category', 'delete_category',
        'create_user', 'view_user', 'edit_user', 'delete_user',
        'view_reports', 'generate_reports',
        'adjust_inventory', 'view_inventory',
        'view_audit_logs'
    },
    'manager': {
        # Can manage most things except users
        'create_sale', 'view_sale', 'cancel_sale', 'add_payment',
        'create_product', 'view_product', 'edit_product', 'delete_product',
        'create_customer', 'view_customer', 'edit_customer', 'delete_customer',
        'create_category', 'view_category', 'edit_category', 'delete_category',
        'view_reports', 'generate_reports',
        'adjust_inventory', 'view_inventory'
    },
    'sales': {
        # Can process sales and view data
        'create_sale', 'view_sale', 'add_payment',
        'view_product', 'view_customer',
        'view_category', 'view_reports'
    },
    'viewer': {
        # Read-only access
        'view_sale', 'view_product', 'view_customer',
        'view_category', 'view_reports', 'view_inventory'
    }
}


def check_permission(user_role: str, action: str) -> bool:
    """Check if a user role has permission to perform an action.

    Args:
        user_role: The user's role (admin, manager, sales, viewer)
        action: The action to check permission for

    Returns:
        True if user has permission, False otherwise
    """
    if user_role not in PERMISSIONS:
        logger.warning(f"Unknown role: {user_role}")
        return False

    return action in PERMISSIONS[user_role]


def get_user_permissions(user_role: str) -> Set[str]:
    """Get all permissions for a given role.

    Args:
        user_role: The user's role

    Returns:
        Set of permission strings
    """
    return PERMISSIONS.get(user_role, set())
