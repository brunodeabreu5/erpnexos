
"""Database initialization module for ERP Paraguay.

This module handles database schema creation and initial data seeding.
It can be run as a standalone script or imported as a module.
"""
import logging
import sys
from sqlalchemy import text
from app.database.db import Base, engine
from app.services.auth_service import create_admin_user
from app.config import setup_logging, ADMIN_PASSWORD

# Set up logging before importing other modules
setup_logging()
logger = logging.getLogger(__name__)

# Columns to add to users if missing (for migration from older schema)
_USERS_TABLE_MIGRATIONS = [
    ("full_name", "VARCHAR(255)"),
    ("email", "VARCHAR(255)"),
    ("role", "VARCHAR(50) NOT NULL DEFAULT 'sales'"),
    ("last_login", "TIMESTAMP WITH TIME ZONE"),
    ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("created_at", "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"),
]


def _migrate_users_table() -> None:
    """Add missing columns to users table for databases created with older schema."""
    with engine.connect() as conn:
        for col_name, col_def in _USERS_TABLE_MIGRATIONS:
            try:
                conn.execute(
                    text(
                        f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                    )
                )
                conn.commit()
            except Exception as e:
                logger.debug("Migration column %s: %s", col_name, e)
                conn.rollback()


def init_db(reset: bool = False) -> bool:
    """Initialize the database schema and create default data.

    Creates all tables defined in the SQLAlchemy models. If reset is True,
    drops all existing tables first (WARNING: this deletes all data).

    Also creates the default admin user if it doesn't exist.

    Args:
        reset: If True, drop all tables before recreating them (DANGEROUS!)

    Returns:
        True if initialization succeeded, False otherwise
    """
    # Validate admin password is configured before proceeding
    if not ADMIN_PASSWORD:
        error_msg = (
            "ADMIN_PASSWORD environment variable not set!\n"
            "Please set ADMIN_PASSWORD in your .env file before initializing the database.\n"
            "Example: ADMIN_PASSWORD=your_secure_password_here"
        )
        logger.error(error_msg)
        return False

    try:
        if reset:
            logger.warning("Reset flag is True - dropping all existing tables")
            Base.metadata.drop_all(bind=engine)
            logger.info("Dropped all existing tables")

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Migrate existing tables (add columns if schema was updated)
        _migrate_users_table()

        # Create default admin user
        logger.info("Ensuring default admin user exists...")
        success, error = create_admin_user()
        if success:
            logger.info("Default admin user is ready")
        else:
            logger.error(f"Failed to create admin user: {error}")
            return False

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False


def main() -> None:
    """Main entry point when running as a standalone script.

    Supports command-line arguments:
        --reset: Drop all tables before recreating (DANGEROUS!)
        --verbose: Enable verbose logging
    """
    import argparse
    from app.config import ADMIN_USERNAME

    parser = argparse.ArgumentParser(
        description="Initialize the ERP Paraguay database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all existing tables before creating new ones (DELETES ALL DATA!)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.reset:
        confirm = input(
            "WARNING: This will DELETE ALL DATA in the database! "
            "Type 'yes' to confirm: "
        )
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(1)

    print("Initializing database...")
    if init_db(reset=args.reset):
        print("Database initialized successfully!")
        print(f"\nAdmin account created with username: {ADMIN_USERNAME}")
        print("Password is configured from ADMIN_PASSWORD environment variable.")
        print("\nIMPORTANT: Keep your .env file secure and never commit it to version control!")
        sys.exit(0)
    else:
        print("\nDatabase initialization failed. Check the following:")
        print("1. Ensure PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file is correct")
        print("3. Ensure ADMIN_PASSWORD is set in .env file")
        print("\nCheck logs for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main()

