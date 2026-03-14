"""Dashboard service module for ERP Paraguay.

Provides dashboard statistics and summary data.
"""
import logging
from typing import Dict
from app.database.db import get_db_session
from app.database.models import Product
from sqlalchemy import func

logger = logging.getLogger(__name__)


def get_dashboard_data() -> Dict[str, int]:
    """Retrieve summary statistics for the dashboard.

    Currently returns counts of products. In production, this would include
    sales figures, revenue, recent activity, etc.

    Returns:
        Dictionary containing dashboard statistics:
        - sales: Number of sales (placeholder, returns 0)
        - products: Number of products in inventory

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            product_count = db.query(func.count(Product.id)).scalar()
            sales_count = 0  # TODO: Implement sales tracking

            logger.info(f"Dashboard data: {product_count} products, {sales_count} sales")
            return {
                "sales": sales_count,
                "products": product_count
            }
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard data: {e}", exc_info=True)
        raise


def get_low_stock_products(threshold: int = 10) -> list:
    """Retrieve products with stock below the given threshold.

    Args:
        threshold: Stock level below which products are considered low stock

    Returns:
        List of Product objects with stock below threshold

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            products = db.query(Product).filter(Product.stock < threshold).all()
            logger.info(f"Found {len(products)} products with stock below {threshold}")
            return products
    except Exception as e:
        logger.error(f"Failed to retrieve low stock products: {e}", exc_info=True)
        raise

