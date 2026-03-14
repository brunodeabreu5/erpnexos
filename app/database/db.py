
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup.

    This context manager ensures that database sessions are properly closed
    after use, preventing connection leaks. It automatically commits on success
    and rolls back on errors.

    Yields:
        Session: SQLAlchemy session object

    Example:
        >>> with get_db_session() as db:
        ...     products = db.query(Product).all()
    """
    db: Optional[Session] = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if db is not None:
            db.close()


@contextmanager
def get_nested_transaction(db: Session) -> Generator[Session, None, None]:
    """Context manager for nested transactions (savepoints).

    This allows creating a transaction within an existing transaction,
    using SAVEPOINT. If the nested transaction fails, it rolls back
    to the savepoint without affecting the outer transaction.

    Args:
        db: The parent database session

    Yields:
        Session: The same session with nested transaction active

    Example:
        >>> with get_db_session() as db:
        ...     # Outer transaction
        ...     customer = db.query(Customer).first()
        ...     with get_nested_transaction(db):
        ...         # Nested transaction (uses SAVEPOINT)
        ...         # If this fails, only this part rolls back
        ...         product = Product(name='Test')
        ...         db.add(product)
    """
    try:
        # Begin nested transaction (SAVEPOINT)
        nested = db.begin_nested()
        yield db
        nested.commit()
    except Exception:
        # Rollback to savepoint on error
        nested.rollback()
        raise


class TransactionManager:
    """Manager for complex multi-step database operations.

    This class provides a convenient way to manage transactions across
    multiple operations, with support for nested transactions and
    automatic rollback on errors.

    Example:
        >>> with TransactionManager() as tm:
        ...     # All operations use the same transaction
        ...     customer = tm.create_customer(...)
        ...     sale = tm.create_sale(...)
        ...     # If anything fails, everything rolls back
    """

    def __init__(self) -> None:
        """Initialize the transaction manager."""
        self.db: Optional[Session] = None
        self._session_owner = False

    def __enter__(self) -> 'TransactionManager':
        """Enter the transaction context.

        Returns:
            TransactionManager: Self for method chaining
        """
        self.db = SessionLocal()
        self._session_owner = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the transaction context.

        Commits if no exception occurred, rolls back otherwise.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.db:
            if exc_type is None:
                self.db.commit()
            else:
                self.db.rollback()
            self.db.close()
            self.db = None

    def commit(self) -> None:
        """Manually commit the transaction."""
        if self.db:
            self.db.commit()

    def rollback(self) -> None:
        """Manually rollback the transaction."""
        if self.db:
            self.db.rollback()

    def nested(self) -> Generator[Session, None, None]:
        """Create a nested transaction context.

        Yields:
            Session: The database session with nested transaction active

        Example:
            >>> with TransactionManager() as tm:
            ...     with tm.nested():
            ...         # This can be rolled back independently
            ...         risky_operation()
        """
        if not self.db:
            raise RuntimeError("TransactionManager not initialized. Use as context manager first.")

        return get_nested_transaction(self.db)

    @property
    def session(self) -> Session:
        """Get the database session.

        Returns:
            Session: The active database session

        Raises:
            RuntimeError: If TransactionManager is not initialized
        """
        if not self.db:
            raise RuntimeError("TransactionManager not initialized. Use as context manager first.")
        return self.db

