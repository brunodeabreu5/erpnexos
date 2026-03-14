"""Supplier service module for ERP Paraguay.

This module provides business logic for supplier and purchase management operations.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from app.database.db import get_db_session
from app.database.models import Supplier, Purchase, PurchaseItem, Product
from app.validators import (
    validate_required_string,
    validate_email,
    validate_phone,
    validate_tax_id,
    validate_sale_items,
    validate_positive_number
)

logger = logging.getLogger(__name__)


def create_supplier(
    name: str,
    contact_person: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    tax_id: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Supplier]]:
    """Create a new supplier in the database.

    Args:
        name: Supplier name (required)
        contact_person: Name of contact person (optional)
        email: Supplier email (optional)
        phone: Contact phone (optional)
        address: Supplier address (optional)
        tax_id: Tax identification (optional, must be unique)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], supplier: Optional[Supplier])
    """
    # Validate inputs
    is_valid, error = validate_required_string(name, "Supplier name")
    if not is_valid:
        return False, error, None

    if email:
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, error, None

    if phone:
        is_valid, error = validate_phone(phone)
        if not is_valid:
            return False, error, None

    if tax_id:
        is_valid, error = validate_tax_id(tax_id)
        if not is_valid:
            return False, error, None

    try:
        with get_db_session() as db:
            # Check for duplicate tax_id
            if tax_id:
                existing = db.query(Supplier).filter(Supplier.tax_id == tax_id).first()
                if existing:
                    return False, "Tax ID already registered", None

            supplier = Supplier(
                name=name.strip(),
                contact_person=contact_person.strip() if contact_person else None,
                email=email.strip() if email else None,
                phone=phone.strip() if phone else None,
                address=address.strip() if address else None,
                tax_id=tax_id.strip().upper() if tax_id else None
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
            logger.info(f"Created supplier: {supplier}")
            return True, None, supplier

    except Exception as e:
        logger.error(f"Failed to create supplier '{name}': {e}", exc_info=True)
        return False, "An error occurred while creating supplier", None


def list_suppliers(active_only: bool = True) -> List[Supplier]:
    """Retrieve all suppliers from the database.

    Args:
        active_only: If True, only return active suppliers

    Returns:
        List of Supplier objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Supplier)
            if active_only:
                query = query.filter(Supplier.is_active == True)
            suppliers = query.order_by(Supplier.name).all()
            logger.info(f"Retrieved {len(suppliers)} suppliers")
            return suppliers
    except Exception as e:
        logger.error(f"Failed to retrieve suppliers: {e}", exc_info=True)
        raise


def list_suppliers_paginated(
    page: int = 1,
    page_size: int = 50,
    active_only: bool = True,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve suppliers with pagination.

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Number of suppliers per page (default: 50)
        active_only: If True, only return active suppliers (default: True)
        search: Optional search term for supplier name or email (default: None)

    Returns:
        Dictionary with:
            - data: List of Supplier objects for current page
            - total: Total number of suppliers matching filters
            - page: Current page number
            - page_size: Number of suppliers per page
            - total_pages: Total number of pages
            - has_next: Whether there's a next page
            - has_prev: Whether there's a previous page

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Supplier)

            # Apply filters
            if active_only:
                query = query.filter(Supplier.is_active == True)

            if search:
                term = f"%{search}%"
                query = query.filter(
                    (Supplier.name.ilike(term)) |
                    (Supplier.email.ilike(term))
                )

            # Get total count
            total = query.count()

            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            offset = (page - 1) * page_size

            # Get paginated results
            suppliers = query.order_by(Supplier.name).offset(offset).limit(page_size).all()

            logger.info(
                f"Retrieved page {page} of {total_pages} "
                f"({len(suppliers)} suppliers, {total} total)"
            )

            return {
                'data': suppliers,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }

    except Exception as e:
        logger.error(f"Failed to retrieve suppliers page {page}: {e}", exc_info=True)
        raise


def get_supplier_by_id(supplier_id: int) -> Optional[Supplier]:
    """Retrieve a single supplier by its ID.

    Args:
        supplier_id: The ID of the supplier to retrieve

    Returns:
        Supplier object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                logger.info(f"Retrieved supplier ID {supplier_id}")
            else:
                logger.warning(f"Supplier ID {supplier_id} not found")
            return supplier
    except Exception as e:
        logger.error(f"Failed to retrieve supplier ID {supplier_id}: {e}", exc_info=True)
        raise


def update_supplier(
    supplier_id: int,
    name: Optional[str] = None,
    contact_person: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    tax_id: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[bool, Optional[str], Optional[Supplier]]:
    """Update an existing supplier.

    Args:
        supplier_id: ID of the supplier to update
        name: New supplier name (optional)
        contact_person: New contact person (optional)
        email: New email (optional)
        phone: New phone (optional)
        address: New address (optional)
        tax_id: New tax ID (optional)
        is_active: New active status (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], supplier: Optional[Supplier])
    """
    try:
        with get_db_session() as db:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                return False, f"Supplier ID {supplier_id} not found", None

            # Validate and update name if provided
            if name is not None:
                is_valid, error = validate_required_string(name, "Supplier name")
                if not is_valid:
                    return False, error, None
                supplier.name = name.strip()

            # Validate and update email if provided
            if email is not None:
                if email:  # Non-empty email
                    is_valid, error = validate_email(email)
                    if not is_valid:
                        return False, error, None
                    # Check for duplicate email
                    existing = db.query(Supplier).filter(
                        Supplier.email == email,
                        Supplier.id != supplier_id
                    ).first()
                    if existing:
                        return False, "Email already registered", None
                    supplier.email = email.strip()
                else:
                    supplier.email = None

            # Validate and update phone if provided
            if phone is not None:
                if phone:  # Non-empty phone
                    is_valid, error = validate_phone(phone)
                    if not is_valid:
                        return False, error, None
                    supplier.phone = phone.strip()
                else:
                    supplier.phone = None

            # Update address if provided
            if address is not None:
                supplier.address = address.strip() if address else None

            # Validate and update tax_id if provided
            if tax_id is not None:
                if tax_id:  # Non-empty tax_id
                    is_valid, error = validate_tax_id(tax_id)
                    if not is_valid:
                        return False, error, None
                    # Check for duplicate tax_id
                    existing = db.query(Supplier).filter(
                        Supplier.tax_id == tax_id,
                        Supplier.id != supplier_id
                    ).first()
                    if existing:
                        return False, "Tax ID already registered", None
                    supplier.tax_id = tax_id.strip().upper()
                else:
                    supplier.tax_id = None

            # Update contact_person if provided
            if contact_person is not None:
                supplier.contact_person = contact_person.strip() if contact_person else None

            # Update is_active if provided
            if is_active is not None:
                supplier.is_active = is_active

            db.commit()
            db.refresh(supplier)
            logger.info(f"Updated supplier ID {supplier_id}: {supplier}")
            return True, None, supplier

    except Exception as e:
        logger.error(f"Failed to update supplier ID {supplier_id}: {e}", exc_info=True)
        return False, "An error occurred while updating supplier", None


def delete_supplier(supplier_id: int) -> Tuple[bool, Optional[str]]:
    """Soft delete a supplier (sets is_active to False).

    Args:
        supplier_id: ID of the supplier to delete

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                return False, f"Supplier ID {supplier_id} not found"

            supplier.is_active = False
            db.commit()
            logger.info(f"Soft deleted supplier ID {supplier_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to delete supplier ID {supplier_id}: {e}", exc_info=True)
        return False, "An error occurred while deleting supplier"


def search_suppliers(search_term: str, active_only: bool = True) -> List[Supplier]:
    """Search for suppliers by name, email, phone, or tax_id.

    Args:
        search_term: The term to search for
        active_only: If True, only search active suppliers

    Returns:
        List of matching Supplier objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            term = f"%{search_term}%"
            query = db.query(Supplier).filter(
                (Supplier.name.ilike(term)) |
                (Supplier.email.ilike(term)) |
                (Supplier.phone.ilike(term)) |
                (Supplier.tax_id.ilike(term)) |
                (Supplier.contact_person.ilike(term))
            )
            if active_only:
                query = query.filter(Supplier.is_active == True)
            suppliers = query.order_by(Supplier.name).all()
            logger.info(f"Found {len(suppliers)} suppliers matching '{search_term}'")
            return suppliers
    except Exception as e:
        logger.error(f"Failed to search suppliers: {e}", exc_info=True)
        raise


def create_purchase(
    supplier_id: int,
    items: List[Dict[str, Any]],
    notes: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[int]]:
    """Create a new purchase from a supplier.

    Args:
        supplier_id: ID of the supplier
        items: List of item dicts with product_id, quantity, unit_cost
        notes: Additional notes

    Returns:
        Tuple of (success: bool, error_message: Optional[str], purchase_id: Optional[int])
    """
    # Validate items
    is_valid, error = validate_sale_items(items)
    if not is_valid:
        return False, error, None

    try:
        with get_db_session() as db:
            # Check supplier exists
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                return False, f"Supplier ID {supplier_id} not found", None

            # Verify products exist
            for item in items:
                product = db.query(Product).filter(Product.id == item['product_id']).first()
                if not product:
                    return False, f"Product ID {item['product_id']} not found", None

            # Calculate totals
            subtotal = Decimal('0')
            for item in items:
                item_subtotal = Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
                subtotal += item_subtotal

            # For now, no tax on purchases (can be added later)
            total = subtotal

            # Create purchase
            purchase = Purchase(
                supplier_id=supplier_id,
                subtotal=float(subtotal),
                total=float(total),
                status='pending',
                notes=notes
            )
            db.add(purchase)
            db.flush()  # Get purchase.id

            # Create purchase items
            for item in items:
                product = db.query(Product).filter(Product.id == item['product_id']).first()
                item_subtotal = Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))

                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item['product_id'],
                    quantity=float(item['quantity']),
                    unit_cost=float(item['unit_cost']),
                    subtotal=float(item_subtotal)
                )
                db.add(purchase_item)

            db.commit()
            logger.info(f"Created purchase ID {purchase.id} for supplier {supplier_id}, total: {total}")
            return True, None, purchase.id

    except Exception as e:
        logger.error(f"Failed to create purchase: {e}", exc_info=True)
        return False, "An error occurred while creating purchase", None


def list_purchases(
    supplier_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None
) -> List[Purchase]:
    """List purchases with optional filters.

    Args:
        supplier_id: Filter by supplier ID (optional)
        start_date: Filter purchases from this date onwards (optional)
        end_date: Filter purchases up to this date (optional)
        status: Filter by status (optional)

    Returns:
        List of Purchase objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Purchase)

            if supplier_id:
                query = query.filter(Purchase.supplier_id == supplier_id)
            if start_date:
                query = query.filter(Purchase.purchase_date >= start_date)
            if end_date:
                query = query.filter(Purchase.purchase_date <= end_date)
            if status:
                query = query.filter(Purchase.status == status)

            purchases = query.order_by(Purchase.purchase_date.desc()).all()
            logger.info(f"Retrieved {len(purchases)} purchases")
            return purchases

    except Exception as e:
        logger.error(f"Failed to list purchases: {e}", exc_info=True)
        raise


def get_purchase_by_id(purchase_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a complete purchase with items.

    Args:
        purchase_id: ID of the purchase to retrieve

    Returns:
        Dictionary with purchase details including items, or None if not found

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
            if not purchase:
                logger.warning(f"Purchase ID {purchase_id} not found")
                return None

            # Get supplier
            supplier = purchase.supplier if purchase else None

            # Build purchase dict
            purchase_dict = {
                'id': purchase.id,
                'supplier_id': purchase.supplier_id,
                'supplier_name': supplier.name if supplier else 'Unknown',
                'purchase_date': purchase.purchase_date,
                'subtotal': float(purchase.subtotal),
                'total': float(purchase.total),
                'status': purchase.status,
                'notes': purchase.notes,
                'items': []
            }

            # Get items
            for item in purchase.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                purchase_dict['items'].append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name if product else 'Unknown',
                    'product_sku': product.sku if product else None,
                    'quantity': float(item.quantity),
                    'unit_cost': float(item.unit_cost),
                    'subtotal': float(item.subtotal)
                })

            logger.info(f"Retrieved purchase ID {purchase_id}")
            return purchase_dict

    except Exception as e:
        logger.error(f"Failed to retrieve purchase ID {purchase_id}: {e}", exc_info=True)
        raise


def receive_purchase(purchase_id: int) -> Tuple[bool, Optional[str]]:
    """Mark a purchase as received and update product stock.

    Args:
        purchase_id: ID of the purchase to receive

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
            if not purchase:
                return False, f"Purchase ID {purchase_id} not found"

            if purchase.status == 'received':
                return False, "Purchase already received"

            # Update stock for all items
            for item in purchase.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock += float(item.quantity)
                    # Update cost price if different
                    if product.cost_price != float(item.unit_cost):
                        product.cost_price = float(item.unit_cost)

            # Update purchase status
            purchase.status = 'received'

            db.commit()
            logger.info(f"Received purchase ID {purchase_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to receive purchase ID {purchase_id}: {e}", exc_info=True)
        return False, "An error occurred while receiving purchase"
