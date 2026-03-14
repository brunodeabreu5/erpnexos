
import logging
from typing import List, Optional
from app.database.db import get_db_session
from app.database.models import Product
from app.validators import (
    validate_product_name,
    validate_positive_number,
    validate_non_negative_number,
    validate_sku
)

logger = logging.getLogger(__name__)


def list_products() -> List[Product]:
    """Retrieve all products from the database.

    Returns:
        List of all Product objects in the database

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            products = db.query(Product).all()
            logger.info(f"Retrieved {len(products)} products")
            return products
    except Exception as e:
        logger.error(f"Failed to retrieve products: {e}", exc_info=True)
        raise


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Retrieve a single product by its ID.

    Args:
        product_id: The ID of the product to retrieve

    Returns:
        Product object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                logger.info(f"Retrieved product ID {product_id}")
            else:
                logger.warning(f"Product ID {product_id} not found")
            return product
    except Exception as e:
        logger.error(f"Failed to retrieve product ID {product_id}: {e}", exc_info=True)
        raise


def create_product(
    name: str,
    price: float,
    stock: float = 0,
    category_id: Optional[int] = None,
    sku: Optional[str] = None,
    cost_price: Optional[float] = None,
    reorder_point: float = 10
) -> Product:
    """Create a new product in the database.

    Args:
        name: Product name
        price: Unit price (must be positive)
        stock: Initial stock quantity (default: 0, must be non-negative)
        category_id: Category ID (optional)
        sku: Stock keeping unit (optional)
        cost_price: Cost price for profit calculation (optional)
        reorder_point: Stock level to trigger reorder (default: 10)

    Returns:
        The created Product object

    Raises:
        ValueError: If validation fails
        Exception: If database operation fails
    """
    # Validate inputs
    is_valid, error = validate_product_name(name)
    if not is_valid:
        raise ValueError(f"Invalid product name: {error}")

    is_valid, error = validate_positive_number(price, "Price")
    if not is_valid:
        raise ValueError(error)

    is_valid, error = validate_non_negative_number(stock, "Stock")
    if not is_valid:
        raise ValueError(error)

    if sku:
        is_valid, error = validate_sku(sku)
        if not is_valid:
            raise ValueError(f"Invalid SKU: {error}")

    if cost_price is not None:
        is_valid, error = validate_non_negative_number(cost_price, "Cost price")
        if not is_valid:
            raise ValueError(error)

    is_valid, error = validate_non_negative_number(reorder_point, "Reorder point")
    if not is_valid:
        raise ValueError(error)

    try:
        with get_db_session() as db:
            # Check for duplicate SKU
            if sku:
                existing = db.query(Product).filter(Product.sku == sku).first()
                if existing:
                    raise ValueError("SKU already exists")

            # Validate category exists if provided
            if category_id is not None:
                from app.database.models import Category
                category = db.query(Category).filter(Category.id == category_id).first()
                if not category:
                    raise ValueError(f"Category ID {category_id} not found")

            product = Product(
                name=name.strip(),
                price=float(price),
                stock=float(stock),
                category_id=category_id,
                sku=sku.strip().upper() if sku else None,
                cost_price=float(cost_price) if cost_price is not None else None,
                reorder_point=float(reorder_point)
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            logger.info(f"Created product: {product}")
            return product
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to create product '{name}': {e}", exc_info=True)
        raise


def update_product(
    product_id: int,
    name: Optional[str] = None,
    price: Optional[float] = None,
    stock: Optional[float] = None,
    category_id: Optional[int] = None,
    sku: Optional[str] = None,
    cost_price: Optional[float] = None,
    reorder_point: Optional[float] = None,
    is_active: Optional[bool] = None
) -> Product:
    """Update an existing product.

    Args:
        product_id: ID of the product to update
        name: New product name (optional)
        price: New price (optional, must be positive if provided)
        stock: New stock quantity (optional, must be non-negative if provided)
        category_id: New category ID (optional)
        sku: New SKU (optional)
        cost_price: New cost price (optional)
        reorder_point: New reorder point (optional)
        is_active: New active status (optional)

    Returns:
        The updated Product object

    Raises:
        ValueError: If product not found or validation fails
        Exception: If database operation fails
    """
    try:
        with get_db_session() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product ID {product_id} not found")

            # Validate and update name if provided
            if name is not None:
                is_valid, error = validate_product_name(name)
                if not is_valid:
                    raise ValueError(f"Invalid product name: {error}")
                product.name = name.strip()

            # Validate and update price if provided
            if price is not None:
                is_valid, error = validate_positive_number(price, "Price")
                if not is_valid:
                    raise ValueError(error)
                product.price = float(price)

            # Validate and update stock if provided
            if stock is not None:
                is_valid, error = validate_non_negative_number(stock, "Stock")
                if not is_valid:
                    raise ValueError(error)
                product.stock = float(stock)

            # Validate and update category if provided
            if category_id is not None:
                from app.database.models import Category
                if category_id > 0:  # 0 or None means no category
                    category = db.query(Category).filter(Category.id == category_id).first()
                    if not category:
                        raise ValueError(f"Category ID {category_id} not found")
                    product.category_id = category_id
                else:
                    product.category_id = None

            # Validate and update SKU if provided
            if sku is not None:
                if sku:  # Non-empty SKU
                    is_valid, error = validate_sku(sku)
                    if not is_valid:
                        raise ValueError(f"Invalid SKU: {error}")
                    # Check for duplicate SKU
                    existing = db.query(Product).filter(
                        Product.sku == sku,
                        Product.id != product_id
                    ).first()
                    if existing:
                        raise ValueError("SKU already exists")
                    product.sku = sku.strip().upper()
                else:  # Empty string, set to None
                    product.sku = None

            # Validate and update cost_price if provided
            if cost_price is not None:
                is_valid, error = validate_non_negative_number(cost_price, "Cost price")
                if not is_valid:
                    raise ValueError(error)
                product.cost_price = float(cost_price) if cost_price > 0 else None

            # Validate and update reorder_point if provided
            if reorder_point is not None:
                is_valid, error = validate_non_negative_number(reorder_point, "Reorder point")
                if not is_valid:
                    raise ValueError(error)
                product.reorder_point = float(reorder_point)

            # Update is_active if provided
            if is_active is not None:
                product.is_active = is_active

            db.commit()
            db.refresh(product)
            logger.info(f"Updated product ID {product_id}: {product}")
            return product

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to update product ID {product_id}: {e}", exc_info=True)
        raise


def delete_product(product_id: int) -> bool:
    """Delete a product from the database.

    Args:
        product_id: ID of the product to delete

    Returns:
        True if product was deleted, False if not found

    Raises:
        Exception: If database operation fails
    """
    try:
        with get_db_session() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Cannot delete: Product ID {product_id} not found")
                return False

            db.delete(product)
            db.commit()
            logger.info(f"Deleted product ID {product_id}")
            return True

    except Exception as e:
        logger.error(f"Failed to delete product ID {product_id}: {e}", exc_info=True)
        raise


def get_products_by_category(category_id: int, active_only: bool = True) -> List[Product]:
    """Retrieve products by category.

    Args:
        category_id: The ID of the category
        active_only: If True, only return active products

    Returns:
        List of Product objects in the category

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Product).filter(Product.category_id == category_id)
            if active_only:
                query = query.filter(Product.is_active == True)
            products = query.order_by(Product.name).all()
            logger.info(f"Retrieved {len(products)} products for category {category_id}")
            return products
    except Exception as e:
        logger.error(f"Failed to retrieve products for category {category_id}: {e}", exc_info=True)
        raise


def search_products(search_term: str, active_only: bool = True) -> List[Product]:
    """Search for products by name or SKU.

    Args:
        search_term: The term to search for
        active_only: If True, only search active products

    Returns:
        List of matching Product objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            term = f"%{search_term}%"
            query = db.query(Product).filter(
                (Product.name.ilike(term)) |
                (Product.sku.ilike(term))
            )
            if active_only:
                query = query.filter(Product.is_active == True)
            products = query.order_by(Product.name).all()
            logger.info(f"Found {len(products)} products matching '{search_term}'")
            return products
    except Exception as e:
        logger.error(f"Failed to search products: {e}", exc_info=True)
        raise

