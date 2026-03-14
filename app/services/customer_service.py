"""Customer service module for ERP Paraguay.

This module provides business logic for customer management operations.

Standard Return Type:
    All operations return Result[Customer] or Result[List[Customer]]:
    - (True, None, data): Success with optional data
    - (False, error_message, None): Failure with error description
"""
import logging
from typing import List, Optional, Dict, Any
from app.database.db import get_db_session
from app.database.models import Customer
from app.types import Result, success, failure
from app.validators import (
    validate_customer_name,
    validate_email,
    validate_phone,
    validate_tax_id
)

logger = logging.getLogger(__name__)


def create_customer(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    tax_id: Optional[str] = None
) -> Result[Customer]:
    """Create a new customer in the database.

    Args:
        name: Customer name (required)
        email: Customer email (optional, must be unique)
        phone: Customer phone (optional)
        address: Customer address (optional)
        tax_id: Tax identification (optional, must be unique)

    Returns:
        Result[Customer]: (True, None, customer) on success,
                          (False, error_message, None) on failure
    """
    # Validate inputs
    is_valid, error = validate_customer_name(name)
    if not is_valid:
        return failure(error)

    if email:
        is_valid, error = validate_email(email)
        if not is_valid:
            return failure(error)

    if phone:
        is_valid, error = validate_phone(phone)
        if not is_valid:
            return failure(error)

    if tax_id:
        is_valid, error = validate_tax_id(tax_id)
        if not is_valid:
            return failure(error)

    try:
        with get_db_session() as db:
            # Check for duplicate email
            if email:
                existing = db.query(Customer).filter(Customer.email == email).first()
                if existing:
                    return failure("Email already registered")

            # Check for duplicate tax_id
            if tax_id:
                existing = db.query(Customer).filter(Customer.tax_id == tax_id).first()
                if existing:
                    return failure("Tax ID already registered")

            customer = Customer(
                name=name.strip(),
                email=email.strip() if email else None,
                phone=phone.strip() if phone else None,
                address=address.strip() if address else None,
                tax_id=tax_id.strip().upper() if tax_id else None
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            logger.info(f"Created customer: {customer}")
            return success(customer)

    except Exception as e:
        logger.error(f"Failed to create customer '{name}': {e}", exc_info=True)
        return failure("An error occurred while creating customer")


def list_customers(active_only: bool = True) -> List[Customer]:
    """Retrieve all customers from the database.

    Args:
        active_only: If True, only return active customers

    Returns:
        List of Customer objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Customer)
            if active_only:
                query = query.filter(Customer.is_active == True)
            customers = query.order_by(Customer.name).all()
            logger.info(f"Retrieved {len(customers)} customers")
            return customers
    except Exception as e:
        logger.error(f"Failed to retrieve customers: {e}", exc_info=True)
        raise


def list_customers_paginated(
    page: int = 1,
    page_size: int = 50,
    active_only: bool = True,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve customers with pagination.

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Number of customers per page (default: 50)
        active_only: If True, only return active customers (default: True)
        search: Optional search term for customer name or email (default: None)

    Returns:
        Dictionary with:
            - data: List of Customer objects for current page
            - total: Total number of customers matching filters
            - page: Current page number
            - page_size: Number of customers per page
            - total_pages: Total number of pages
            - has_next: Whether there's a next page
            - has_prev: Whether there's a previous page

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Customer)

            # Apply filters
            if active_only:
                query = query.filter(Customer.is_active == True)

            if search:
                term = f"%{search}%"
                query = query.filter(
                    (Customer.name.ilike(term)) |
                    (Customer.email.ilike(term))
                )

            # Get total count
            total = query.count()

            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            offset = (page - 1) * page_size

            # Get paginated results
            customers = query.order_by(Customer.name).offset(offset).limit(page_size).all()

            logger.info(
                f"Retrieved page {page} of {total_pages} "
                f"({len(customers)} customers, {total} total)"
            )

            return {
                'data': customers,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }

    except Exception as e:
        logger.error(f"Failed to retrieve customers page {page}: {e}", exc_info=True)
        raise


def get_customer_by_id(customer_id: int) -> Optional[Customer]:
    """Retrieve a single customer by its ID.

    Args:
        customer_id: The ID of the customer to retrieve

    Returns:
        Customer object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                logger.info(f"Retrieved customer ID {customer_id}")
            else:
                logger.warning(f"Customer ID {customer_id} not found")
            return customer
    except Exception as e:
        logger.error(f"Failed to retrieve customer ID {customer_id}: {e}", exc_info=True)
        raise


def update_customer(
    customer_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    tax_id: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[bool, Optional[str], Optional[Customer]]:
    """Update an existing customer.

    Args:
        customer_id: ID of the customer to update
        name: New customer name (optional)
        email: New email (optional)
        phone: New phone (optional)
        address: New address (optional)
        tax_id: New tax ID (optional)
        is_active: New active status (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], customer: Optional[Customer])
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False, f"Customer ID {customer_id} not found", None

            # Validate and update name if provided
            if name is not None:
                is_valid, error = validate_customer_name(name)
                if not is_valid:
                    return False, error, None
                customer.name = name.strip()

            # Validate and update email if provided
            if email is not None:
                if email:  # Non-empty email
                    is_valid, error = validate_email(email)
                    if not is_valid:
                        return False, error, None
                    # Check for duplicate email
                    existing = db.query(Customer).filter(
                        Customer.email == email,
                        Customer.id != customer_id
                    ).first()
                    if existing:
                        return False, "Email already registered", None
                    customer.email = email.strip()
                else:  # Empty string, set to None
                    customer.email = None

            # Validate and update phone if provided
            if phone is not None:
                if phone:  # Non-empty phone
                    is_valid, error = validate_phone(phone)
                    if not is_valid:
                        return False, error, None
                    customer.phone = phone.strip()
                else:
                    customer.phone = None

            # Update address if provided
            if address is not None:
                customer.address = address.strip() if address else None

            # Validate and update tax_id if provided
            if tax_id is not None:
                if tax_id:  # Non-empty tax_id
                    is_valid, error = validate_tax_id(tax_id)
                    if not is_valid:
                        return False, error, None
                    # Check for duplicate tax_id
                    existing = db.query(Customer).filter(
                        Customer.tax_id == tax_id,
                        Customer.id != customer_id
                    ).first()
                    if existing:
                        return False, "Tax ID already registered", None
                    customer.tax_id = tax_id.strip().upper()
                else:
                    customer.tax_id = None

            # Update is_active if provided
            if is_active is not None:
                customer.is_active = is_active

            db.commit()
            db.refresh(customer)
            logger.info(f"Updated customer ID {customer_id}: {customer}")
            return True, None, customer

    except Exception as e:
        logger.error(f"Failed to update customer ID {customer_id}: {e}", exc_info=True)
        return False, "An error occurred while updating customer", None


def delete_customer(customer_id: int) -> Tuple[bool, Optional[str]]:
    """Soft delete a customer (sets is_active to False).

    Args:
        customer_id: ID of the customer to delete

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False, f"Customer ID {customer_id} not found"

            customer.is_active = False
            db.commit()
            logger.info(f"Soft deleted customer ID {customer_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to delete customer ID {customer_id}: {e}", exc_info=True)
        return False, "An error occurred while deleting customer"


def search_customers(search_term: str, active_only: bool = True) -> List[Customer]:
    """Search for customers by name, email, phone, or tax_id.

    Args:
        search_term: The term to search for
        active_only: If True, only search active customers

    Returns:
        List of matching Customer objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            term = f"%{search_term}%"
            query = db.query(Customer).filter(
                (Customer.name.ilike(term)) |
                (Customer.email.ilike(term)) |
                (Customer.phone.ilike(term)) |
                (Customer.tax_id.ilike(term))
            )
            if active_only:
                query = query.filter(Customer.is_active == True)
            customers = query.order_by(Customer.name).all()
            logger.info(f"Found {len(customers)} customers matching '{search_term}'")
            return customers
    except Exception as e:
        logger.error(f"Failed to search customers: {e}", exc_info=True)
        raise
