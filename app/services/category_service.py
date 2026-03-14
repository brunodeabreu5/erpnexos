"""Category service module for ERP Paraguay.

This module provides business logic for category management operations.
"""
import logging
from typing import List, Optional, Tuple
from app.database.db import get_db_session
from app.database.models import Category
from app.validators import validate_category_name

logger = logging.getLogger(__name__)


def create_category(
    name: str,
    description: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Category]]:
    """Create a new category in the database.

    Args:
        name: Category name (required, must be unique)
        description: Category description (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], category: Optional[Category])
    """
    # Validate inputs
    is_valid, error = validate_category_name(name)
    if not is_valid:
        return False, error, None

    try:
        with get_db_session() as db:
            # Check for duplicate name
            existing = db.query(Category).filter(Category.name == name.strip()).first()
            if existing:
                return False, "Category name already exists", None

            category = Category(
                name=name.strip(),
                description=description.strip() if description else None
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            logger.info(f"Created category: {category}")
            return True, None, category

    except Exception as e:
        logger.error(f"Failed to create category '{name}': {e}", exc_info=True)
        return False, "An error occurred while creating category", None


def list_categories(active_only: bool = True) -> List[Category]:
    """Retrieve all categories from the database.

    Args:
        active_only: If True, only return active categories

    Returns:
        List of Category objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Category)
            if active_only:
                query = query.filter(Category.is_active == True)
            categories = query.order_by(Category.name).all()
            logger.info(f"Retrieved {len(categories)} categories")
            return categories
    except Exception as e:
        logger.error(f"Failed to retrieve categories: {e}", exc_info=True)
        raise


def get_category_by_id(category_id: int) -> Optional[Category]:
    """Retrieve a single category by its ID.

    Args:
        category_id: The ID of the category to retrieve

    Returns:
        Category object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                logger.info(f"Retrieved category ID {category_id}")
            else:
                logger.warning(f"Category ID {category_id} not found")
            return category
    except Exception as e:
        logger.error(f"Failed to retrieve category ID {category_id}: {e}", exc_info=True)
        raise


def update_category(
    category_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[bool, Optional[str], Optional[Category]]:
    """Update an existing category.

    Args:
        category_id: ID of the category to update
        name: New category name (optional)
        description: New description (optional)
        is_active: New active status (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], category: Optional[Category])
    """
    try:
        with get_db_session() as db:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                return False, f"Category ID {category_id} not found", None

            # Validate and update name if provided
            if name is not None:
                is_valid, error = validate_category_name(name)
                if not is_valid:
                    return False, error, None
                # Check for duplicate name
                existing = db.query(Category).filter(
                    Category.name == name.strip(),
                    Category.id != category_id
                ).first()
                if existing:
                    return False, "Category name already exists", None
                category.name = name.strip()

            # Update description if provided
            if description is not None:
                category.description = description.strip() if description else None

            # Update is_active if provided
            if is_active is not None:
                category.is_active = is_active

            db.commit()
            db.refresh(category)
            logger.info(f"Updated category ID {category_id}: {category}")
            return True, None, category

    except Exception as e:
        logger.error(f"Failed to update category ID {category_id}: {e}", exc_info=True)
        return False, "An error occurred while updating category", None


def delete_category(category_id: int) -> Tuple[bool, Optional[str]]:
    """Soft delete a category (sets is_active to False).

    Args:
        category_id: ID of the category to delete

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                return False, f"Category ID {category_id} not found"

            category.is_active = False
            db.commit()
            logger.info(f"Soft deleted category ID {category_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to delete category ID {category_id}: {e}", exc_info=True)
        return False, "An error occurred while deleting category"


def get_categories_count() -> int:
    """Get the total count of active categories.

    Returns:
        Number of active categories

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            count = db.query(Category).filter(Category.is_active == True).count()
            return count
    except Exception as e:
        logger.error(f"Failed to count categories: {e}", exc_info=True)
        raise
