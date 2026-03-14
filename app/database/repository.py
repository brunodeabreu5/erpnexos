"""Repository pattern implementation for ERP Paraguay.

This module provides a base repository class with generic CRUD operations
to reduce code duplication across service modules.
"""
import logging
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database.db import get_db_session

logger = logging.getLogger(__name__)

# Generic type for model classes
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with generic CRUD operations.

    This class provides common database operations that can be reused
    across different entity types. It eliminates code duplication and
    provides a consistent interface for data access.

    Type Parameters:
        T: The SQLAlchemy model class (e.g., Product, Customer, etc.)

    Example:
        class ProductRepository(BaseRepository[Product]):
            def __init__(self):
                super().__init__(Product)

        repo = ProductRepository()
        all_products = repo.get_all()
        product = repo.get_by_id(1)
    """

    def __init__(self, model: Type[T]) -> None:
        """Initialize the repository with a model class.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model
        self.model_name = model.__name__

    def get_all(
        self,
        active_only: bool = False,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[T]:
        """Retrieve all records of the model type.

        Args:
            active_only: If True and model has is_active field, only return active records
            order_by: Field name to order by (optional)
            descending: If True, order in descending order (default: False)

        Returns:
            List of model instances

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                query = db.query(self.model)

                # Filter by active status if requested and field exists
                if active_only and hasattr(self.model, 'is_active'):
                    query = query.filter(self.model.is_active == True)

                # Apply ordering if specified
                if order_by and hasattr(self.model, order_by):
                    order_field = getattr(self.model, order_by)
                    query = query.order_by(desc(order_field) if descending else order_field)

                results = query.all()
                logger.info(f"Retrieved {len(results)} {self.model_name} records")
                return results

        except Exception as e:
            logger.error(f"Failed to retrieve {self.model_name} records: {e}", exc_info=True)
            raise

    def get_by_id(self, record_id: int) -> Optional[T]:
        """Retrieve a single record by ID.

        Args:
            record_id: The ID of the record to retrieve

        Returns:
            Model instance if found, None otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                record = db.query(self.model).filter(self.model.id == record_id).first()
                if record:
                    logger.info(f"Retrieved {self.model_name} ID {record_id}")
                else:
                    logger.warning(f"{self.model_name} ID {record_id} not found")
                return record

        except Exception as e:
            logger.error(f"Failed to retrieve {self.model_name} ID {record_id}: {e}", exc_info=True)
            raise

    def create(self, **kwargs) -> T:
        """Create a new record.

        Args:
            **kwargs: Field names and values for the new record

        Returns:
            The created model instance

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_db_session() as db:
                record = self.model(**kwargs)
                db.add(record)
                db.commit()
                db.refresh(record)
                logger.info(f"Created {self.model_name}: {record}")
                return record

        except Exception as e:
            logger.error(f"Failed to create {self.model_name}: {e}", exc_info=True)
            raise

    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """Update an existing record.

        Args:
            record_id: ID of the record to update
            **kwargs: Field names and values to update

        Returns:
            The updated model instance, or None if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_db_session() as db:
                record = db.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    logger.warning(f"Cannot update: {self.model_name} ID {record_id} not found")
                    return None

                # Update fields
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                    else:
                        logger.warning(f"Field {key} does not exist on {self.model_name}")

                db.commit()
                db.refresh(record)
                logger.info(f"Updated {self.model_name} ID {record_id}")
                return record

        except Exception as e:
            logger.error(f"Failed to update {self.model_name} ID {record_id}: {e}", exc_info=True)
            raise

    def delete(self, record_id: int) -> bool:
        """Delete a record by ID.

        Args:
            record_id: ID of the record to delete

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_db_session() as db:
                record = db.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    logger.warning(f"Cannot delete: {self.model_name} ID {record_id} not found")
                    return False

                db.delete(record)
                db.commit()
                logger.info(f"Deleted {self.model_name} ID {record_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete {self.model_name} ID {record_id}: {e}", exc_info=True)
            raise

    def filter(self, **filters) -> List[T]:
        """Filter records by field values.

        Args:
            **filters: Field names and values to filter by

        Returns:
            List of matching model instances

        Raises:
            Exception: If database query fails

        Example:
            repo.filter(name='Product A', is_active=True)
        """
        try:
            with get_db_session() as db:
                query = db.query(self.model)

                # Apply filters
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        field = getattr(self.model, key)
                        query = query.filter(field == value)
                    else:
                        logger.warning(f"Filter field {key} does not exist on {self.model_name}")

                results = query.all()
                logger.info(f"Found {len(results)} {self.model_name} records matching filters")
                return results

        except Exception as e:
            logger.error(f"Failed to filter {self.model_name} records: {e}", exc_info=True)
            raise

    def search(
        self,
        search_term: str,
        search_fields: Optional[List[str]] = None,
        active_only: bool = True
    ) -> List[T]:
        """Search records by term across specified fields.

        Args:
            search_term: The term to search for
            search_fields: List of field names to search in (default: ['name'])
            active_only: If True, only search active records

        Returns:
            List of matching model instances

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                # Default search fields if not specified
                if search_fields is None:
                    search_fields = ['name']
                    if not hasattr(self.model, 'name'):
                        search_fields = []
                        # Try to find string fields
                        for column in self.model.__table__.columns:
                            if str(column.type) in ('VARCHAR', 'TEXT'):
                                search_fields.append(column.name)

                if not search_fields:
                    logger.warning(f"No searchable fields found for {self.model_name}")
                    return []

                # Build search query
                query = db.query(self.model)
                term = f"%{search_term}%"

                # Create OR conditions for all search fields
                from sqlalchemy import or_
                conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        field_obj = getattr(self.model, field)
                        conditions.append(field_obj.ilike(term))

                if conditions:
                    query = query.filter(or_(*conditions))

                # Filter by active status if requested
                if active_only and hasattr(self.model, 'is_active'):
                    query = query.filter(self.model.is_active == True)

                results = query.all()
                logger.info(f"Found {len(results)} {self.model_name} records matching '{search_term}'")
                return results

        except Exception as e:
            logger.error(f"Failed to search {self.model_name} records: {e}", exc_info=True)
            raise

    def get_page(
        self,
        page: int = 1,
        page_size: int = 50,
        active_only: bool = False,
        order_by: Optional[str] = None,
        descending: bool = False,
        **filters
    ) -> Dict[str, Any]:
        """Get paginated results with metadata.

        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            active_only: If True, only return active records
            order_by: Field name to order by (optional)
            descending: If True, order in descending order
            **filters: Additional filters to apply

        Returns:
            Dictionary with:
                - data: List of records for the current page
                - total: Total number of records matching filters
                - page: Current page number
                - page_size: Number of records per page
                - total_pages: Total number of pages

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                query = db.query(self.model)

                # Apply filters
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        field = getattr(self.model, key)
                        query = query.filter(field == value)

                # Filter by active status if requested
                if active_only and hasattr(self.model, 'is_active'):
                    query = query.filter(self.model.is_active == True)

                # Get total count
                total = query.count()

                # Apply ordering
                if order_by and hasattr(self.model, order_by):
                    order_field = getattr(self.model, order_by)
                    query = query.order_by(desc(order_field) if descending else order_field)

                # Apply pagination
                offset = (page - 1) * page_size
                data = query.offset(offset).limit(page_size).all()

                total_pages = (total + page_size - 1) // page_size  # Ceiling division

                result = {
                    'data': data,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }

                logger.info(
                    f"Retrieved page {page} of {total_pages} "
                    f"({len(data)} records, {total} total)"
                )
                return result

        except Exception as e:
            logger.error(f"Failed to get paginated {self.model_name} records: {e}", exc_info=True)
            raise

    def count(self, **filters) -> int:
        """Count records matching filters.

        Args:
            **filters: Field names and values to filter by

        Returns:
            Count of matching records

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                query = db.query(self.model)

                # Apply filters
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        field = getattr(self.model, key)
                        query = query.filter(field == value)

                count = query.count()
                logger.info(f"Counted {count} {self.model_name} records")
                return count

        except Exception as e:
            logger.error(f"Failed to count {self.model_name} records: {e}", exc_info=True)
            raise

    def exists(self, record_id: int) -> bool:
        """Check if a record exists by ID.

        Args:
            record_id: ID to check

        Returns:
            True if record exists, False otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            with get_db_session() as db:
                return db.query(self.model).filter(self.model.id == record_id).first() is not None

        except Exception as e:
            logger.error(f"Failed to check {self.model_name} existence: {e}", exc_info=True)
            raise
