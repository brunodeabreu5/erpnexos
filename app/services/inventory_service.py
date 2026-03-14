"""Inventory service module for ERP Paraguay.

This module provides business logic for inventory management operations.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from app.database.db import get_db_session
from app.database.models import Product
from app.validators import validate_positive_number

logger = logging.getLogger(__name__)


def adjust_stock(
    product_id: int,
    quantity: float,
    reason: str,
    reference_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """Manually adjust product stock.

    Args:
        product_id: ID of the product
        quantity: Quantity to adjust (positive to add, negative to remove)
        reason: Reason for adjustment
        reference_id: Optional reference ID (e.g., sale_id, purchase_id)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False, f"Product ID {product_id} not found"

            # Check if we have enough stock for negative adjustments
            new_stock = product.stock + quantity
            if new_stock < 0:
                return False, f"Insufficient stock. Current: {product.stock}, Attempted adjustment: {quantity}"

            # Adjust stock
            old_stock = product.stock
            product.stock = new_stock

            db.commit()
            logger.info(f"Stock adjusted for product {product_id}: {old_stock} -> {new_stock}. Reason: {reason}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to adjust stock for product {product_id}: {e}", exc_info=True)
        return False, "An error occurred while adjusting stock"


def get_reorder_products(threshold: Optional[float] = None) -> List[Product]:
    """Get products that need reordering (stock below reorder point).

    Args:
        threshold: Override threshold (uses product.reorder_point if None)

    Returns:
        List of products that need reordering

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            if threshold is not None:
                products = db.query(Product).filter(
                    Product.is_active == True,
                    Product.stock <= threshold
                ).all()
            else:
                # Use each product's reorder_point
                products = db.query(Product).filter(
                    Product.is_active == True,
                    Product.stock <= Product.reorder_point
                ).all()

            logger.info(f"Found {len(products)} products needing reorder")
            return products

    except Exception as e:
        logger.error(f"Failed to get reorder products: {e}", exc_info=True)
        raise


def get_stock_movements(
    product_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Get stock movement history for a product.

    Note: This is a simplified version. A full implementation would have
    a StockMovement table to track all changes.

    Args:
        product_id: ID of the product
        start_date: Start date filter (optional)
        end_date: End date filter (optional)

    Returns:
        List of stock movement dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product ID {product_id} not found")
                return []

            # For now, return current stock info
            # A full implementation would query a StockMovement table
            movements = [{
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': float(product.stock),
                'reorder_point': float(product.reorder_point),
                'needs_reorder': float(product.stock) <= float(product.reorder_point),
                'note': 'Full stock history requires StockMovement table implementation'
            }]

            return movements

    except Exception as e:
        logger.error(f"Failed to get stock movements for product {product_id}: {e}", exc_info=True)
        raise


def bulk_update_stock(updates: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Update stock for multiple products in a single transaction.

    Args:
        updates: List of dicts with product_id and quantity

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            for update in updates:
                if 'product_id' not in update or 'quantity' not in update:
                    return False, "Each update must have product_id and quantity"

                product = db.query(Product).filter(Product.id == update['product_id']).first()
                if not product:
                    return False, f"Product ID {update['product_id']} not found"

                new_stock = product.stock + update['quantity']
                if new_stock < 0:
                    return False, f"Insufficient stock for product '{product.name}'. Current: {product.stock}, Attempted: {update['quantity']}"

                product.stock = new_stock

            db.commit()
            logger.info(f"Bulk stock update completed for {len(updates)} products")
            return True, None

    except Exception as e:
        logger.error(f"Failed bulk stock update: {e}", exc_info=True)
        return False, "An error occurred during bulk stock update"


def get_inventory_value() -> Dict[str, Any]:
    """Calculate total inventory value.

    Returns:
        Dictionary with inventory value statistics

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            products = db.query(Product).filter(Product.is_active == True).all()

            total_value = sum(float(p.price) * float(p.stock) for p in products)
            total_cost = sum(
                (float(p.cost_price) if p.cost_price else 0) * float(p.stock)
                for p in products
            )
            total_items = sum(float(p.stock) for p in products)

            return {
                'total_products': len(products),
                'total_items': float(total_items),
                'total retail_value': float(total_value),
                'total_cost_value': float(total_cost),
                'potential_profit': float(total_value - total_cost)
            }

    except Exception as e:
        logger.error(f"Failed to calculate inventory value: {e}", exc_info=True)
        raise


def get_purchase_history(product_id: int) -> List[Dict[str, Any]]:
    """Get purchase history for a specific product.

    Args:
        product_id: ID of the product

    Returns:
        List of purchase history dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        from app.database.models import Purchase, PurchaseItem, Supplier

        with get_db_session() as db:
            # Get all purchase items for this product
            purchase_items = db.query(PurchaseItem).filter(
                PurchaseItem.product_id == product_id
            ).all()

            history = []
            for item in purchase_items:
                purchase = db.query(Purchase).filter(Purchase.id == item.purchase_id).first()
                if purchase:
                    supplier = db.query(Supplier).filter(Supplier.id == purchase.supplier_id).first()
                    history.append({
                        'purchase_id': purchase.id,
                        'purchase_date': purchase.purchase_date,
                        'supplier_name': supplier.name if supplier else 'Unknown',
                        'quantity': float(item.quantity),
                        'unit_cost': float(item.unit_cost),
                        'subtotal': float(item.subtotal),
                        'status': purchase.status
                    })

            # Sort by date descending
            history.sort(key=lambda x: x['purchase_date'], reverse=True)
            return history

    except Exception as e:
        logger.error(f"Failed to get purchase history for product {product_id}: {e}", exc_info=True)
        raise


def get_stock_adjustments_with_reference(
    reference_type: str,
    reference_id: int
) -> List[Dict[str, Any]]:
    """Get stock adjustments by reference (e.g., all adjustments from a purchase).

    Args:
        reference_type: Type of reference ('purchase', 'sale', 'adjustment')
        reference_id: ID of the reference

    Returns:
        List of stock adjustment dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # This is a simplified version - a full implementation would query a StockMovement table
            if reference_type == 'purchase':
                from app.database.models import Purchase, PurchaseItem

                purchase = db.query(Purchase).filter(Purchase.id == reference_id).first()
                if not purchase:
                    return []

                items = []
                for item in purchase.items:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    if product:
                        items.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'quantity': float(item.quantity),
                            'type': 'in',
                            'reason': f'Purchase #{purchase.id}',
                            'date': purchase.purchase_date
                        })

                return items

            # For other reference types, return empty list for now
            return []

    except Exception as e:
        logger.error(f"Failed to get stock adjustments for {reference_type} {reference_id}: {e}", exc_info=True)
        raise
