import os
import json
import logging
import uuid
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL: str = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable must be set. "
        "Create a .env file with DATABASE_URL=postgresql://user:password@localhost:5432/erp_paraguay"
    )

# Application Settings
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()

# Validate log level
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
if LOG_LEVEL not in VALID_LOG_LEVELS:
    raise ValueError(f"LOG_LEVEL must be one of {VALID_LOG_LEVELS}, got '{LOG_LEVEL}'")

# Validate environment
VALID_ENVIRONMENTS = {"development", "staging", "production"}
if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(f"ENVIRONMENT must be one of {VALID_ENVIRONMENTS}, got '{ENVIRONMENT}'")

# Database Connection Pool Settings
DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Security Settings
MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "6"))
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_BLOCK_MINUTES: int = int(os.getenv("LOGIN_BLOCK_MINUTES", "15"))

# Context tracking for logging
_request_context = threading.local()


def set_request_context(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """Set context for the current request/thread for logging.

    Args:
        user_id: Optional ID of the current user
        username: Optional username of the current user
        request_id: Optional request ID for tracking
        **kwargs: Additional context key-value pairs
    """
    context = {}

    if user_id is not None:
        context['user_id'] = user_id
    if username is not None:
        context['username'] = username
    if request_id is not None:
        context['request_id'] = request_id
    context.update(kwargs)

    _request_context.value = context


def get_request_context() -> Dict[str, Any]:
    """Get the current request context.

    Returns:
        Dictionary with context information
    """
    return getattr(_request_context, 'value', {})


def clear_request_context() -> None:
    """Clear the current request context."""
    _request_context.value = {}


def generate_request_id() -> str:
    """Generate a unique request ID for tracking.

    Returns:
        Unique request ID string
    """
    return str(uuid.uuid4())


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs logs in structured JSON format.

    This formatter adds contextual information (user_id, request_id, etc.)
    to each log entry for better traceability and debugging.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        # Get request context
        context = get_request_context()

        # Create log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'environment': ENVIRONMENT,
        }

        # Add context if available
        if context:
            log_data.update(context)

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }

        # Add stack trace for ERROR level and above
        if record.levelno >= logging.ERROR and not record.exc_info:
            log_data['stack_trace'] = self.formatStack(record.stack_info) if record.stack_info else None

        return json.dumps(log_data)

# Logging Configuration
LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE: Path = LOG_DIR / "app.log"
LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))


def setup_logging() -> None:
    """Configure application logging with structured output.

    Sets up logging with:
    - Structured JSON logging for production
    - Human-readable logging for development
    - Rotating file handler with configurable size and retention
    - Console handler for development/debugging
    - Context tracking (user_id, request_id) in all log entries

    The log directory is created if it doesn't exist.
    """
    import logging
    from logging.handlers import RotatingFileHandler

    # Create logs directory if it doesn't exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Clear existing handlers
    logger.handlers.clear()

    # Choose formatter based on environment
    if ENVIRONMENT == 'production':
        # Use structured JSON logging in production
        file_formatter = StructuredFormatter()
    else:
        # Use human-readable format in development
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console formatter (always human-readable)
    console_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def validate_configuration() -> bool:
    """Validate all application configuration at startup.

    Checks that all required settings are properly configured for the
    current environment. Logs warnings for missing optional settings
    and errors for missing critical settings.

    Returns:
        True if all critical validation passes, False otherwise
    """
    import logging
    logger_local = logging.getLogger(__name__)
    logger_local.info(f"Validating configuration for environment: {ENVIRONMENT}")

    errors = []
    warnings = []

    # Critical security settings - always required
    if not ADMIN_PASSWORD:
        errors.append("ADMIN_PASSWORD is not set. This is required for application startup.")
    elif ADMIN_PASSWORD in ['admin123', 'your_secure_admin_password_here']:
        warnings.append("ADMIN_PASSWORD is using a default value. Please change it in production.")

    # Database validation
    if not DATABASE_URL:
        errors.append("DATABASE_URL is not set.")
    elif 'your_secure_password' in DATABASE_URL:
        warnings.append("DATABASE_URL contains default password. Please update with actual database password.")

    # Environment-specific validation
    if ENVIRONMENT == 'production':
        # Production requires more strict settings
        if DEBUG:
            errors.append("DEBUG cannot be true in production environment.")

        if LOG_LEVEL == 'DEBUG':
            warnings.append("LOG_LEVEL should not be DEBUG in production (too verbose).")

        if MIN_PASSWORD_LENGTH < 8:
            errors.append("MIN_PASSWORD_LENGTH must be at least 8 in production.")

        if SESSION_TIMEOUT_MINUTES > 60:
            warnings.append(f"SESSION_TIMEOUT_MINUTES is {SESSION_TIMEOUT_MINUTES} minutes. Recommended: 30-60 minutes for production.")

    elif ENVIRONMENT == 'development':
        # Development environment specific checks
        if not DEBUG:
            warnings.append("DEBUG is false in development. Consider enabling for better error messages.")

        if LOG_LEVEL != 'DEBUG':
            warnings.append(f"LOG_LEVEL is {LOG_LEVEL}. Consider DEBUG in development.")

    elif ENVIRONMENT == 'staging':
        # Staging environment
        if DEBUG:
            warnings.append("DEBUG is true in staging. Should typically be false.")

    # Log warnings
    for warning in warnings:
        logger_local.warning(f"Configuration warning: {warning}")

    # Log errors and fail if critical errors exist
    if errors:
        for error in errors:
            logger_local.error(f"Configuration error: {error}")
        logger_local.error("Application cannot start due to configuration errors. Please fix the issues above.")
        return False

    logger_local.info("Configuration validation passed successfully.")
    return True
