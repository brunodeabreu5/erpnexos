"""Sales management service module for ERP Paraguay.

This module provides business logic for sales processing and management.
All operations use atomic transactions to ensure data consistency.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from app.database.db import get_db_session, TransactionManager
from app.database.models import Sale, SaleItem, Payment, Product, Customer
from app.exceptions import (
    CustomerNotFoundError,
    ProductNotFoundError,
    InsufficientStockError,
    BusinessRuleError
)
from app.validators import (
    validate_sale_items,
    validate_payment_method,
    validate_discount
)
from app.settings import TaxSettings

logger = logging.getLogger(__name__)


def create_sale(
    customer_id: int,
    items: List[Dict[str, Any]],
    payment_method: str,
    discount: float = 0,
    notes: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[int]]:
    """Create a complete sale with items and stock deduction.

    This function performs multiple database operations atomically:
    1. Validates customer exists
    2. Validates stock availability for all items
    3. Calculates totals (subtotal, tax, discount, total)
    4. Creates Sale and SaleItems
    5. Deducts stock from products
    6. Creates Payment if paid upfront
    7. Updates customer balance if credit sale

    All operations use a single atomic transaction - if any step fails,
    all changes are rolled back automatically.

    Args:
        customer_id: ID of the customer
        items: List of item dicts with product_id, quantity, unit_price, discount
        payment_method: Payment method (cash, transfer, card, credit)
        discount: Overall discount amount (default: 0)
        notes: Additional notes

    Returns:
        Tuple of (success: bool, error_message: Optional[str], sale_id: Optional[int])
    """
    # Validate payment method
    is_valid, error = validate_payment_method(payment_method)
    if not is_valid:
        return False, error, None

    # Validate discount
    if discount > 0:
        is_valid, error = validate_discount(discount)
        if not is_valid:
            return False, error, None

    # Validate sale items
    is_valid, error = validate_sale_items(items)
    if not is_valid:
        return False, error, None

    # Use TransactionManager for atomic transaction across all operations
    try:
        with TransactionManager() as tm:
            db = tm.session

            # Check customer exists
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise CustomerNotFoundError(customer_id)

            # Verify stock availability for all items
            for item in items:
                product = db.query(Product).filter(Product.id == item['product_id']).first()
                if not product:
                    raise ProductNotFoundError(item['product_id'])
                if not product.is_active:
                    raise BusinessRuleError(
                        f"Product '{product.name}' is not active",
                        rule_name='product_active'
                    )
                if product.stock < item['quantity']:
                    raise InsufficientStockError(
                        product_name=product.name,
                        requested=float(item['quantity']),
                        available=float(product.stock)
                    )

            # Calculate totals
            subtotal = Decimal('0')
            for item in items:
                item_subtotal = Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
                item_discount = Decimal(str(item.get('discount', 0)))
                subtotal += (item_subtotal - item_discount)

            # Apply overall discount
            overall_discount = Decimal(str(discount))
            discounted_subtotal = max(subtotal - overall_discount, Decimal('0'))

            # Calculate tax
            tax_amount = discounted_subtotal * Decimal(str(TaxSettings.RATE))

            # Calculate total
            total = discounted_subtotal + tax_amount

            # Create sale
            sale = Sale(
                customer_id=customer_id,
                subtotal=float(subtotal),
                tax_amount=float(tax_amount),
                discount_amount=float(overall_discount),
                total=float(total),
                payment_method=payment_method.lower(),
                payment_status='paid' if payment_method.lower() != 'credit' else 'pending',
                notes=notes,
                status='completed'
            )
            db.add(sale)
            db.flush()  # Get sale.id

            # Use nested transaction for sale items and stock updates
            # If this part fails, we can handle it specifically
            with tm.nested():
                # Create sale items and update stock
                for item in items:
                    product = db.query(Product).filter(Product.id == item['product_id']).first()
                    item_subtotal = Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
                    item_discount = Decimal(str(item.get('discount', 0)))
                    item_total = item_subtotal - item_discount

                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_id=item['product_id'],
                        quantity=float(item['quantity']),
                        unit_price=float(item['unit_price']),
                        subtotal=float(item_subtotal),
                        discount=float(item_discount),
                        total=float(item_total)
                    )
                    db.add(sale_item)

                    # Deduct stock (atomic with item creation)
                    product.stock -= float(item['quantity'])

            # Create payment if not credit sale
            if payment_method.lower() != 'credit':
                payment = Payment(
                    sale_id=sale.id,
                    amount=float(total),
                    payment_method=payment_method.lower(),
                    notes="Initial payment"
                )
                db.add(payment)
            else:
                # Update customer balance for credit sales
                customer.balance += float(total)

            # TransactionManager commits automatically on success
            logger.info(
                f"Created sale ID {sale.id} for customer {customer_id}, "
                f"total: {total}, items: {len(items)}"
            )
            return True, None, sale.id

    except (CustomerNotFoundError, ProductNotFoundError, InsufficientStockError, BusinessRuleError) as e:
        # Custom exceptions - already logged and detailed
        logger.warning(f"Sale creation failed: {e.message}")
        return False, e.message, None
    except Exception as e:
        logger.error(f"Failed to create sale: {e}", exc_info=True)
        return False, "An error occurred while creating sale", None


def get_sale_by_id(sale_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a complete sale with items and payments.

    Args:
        sale_id: ID of the sale to retrieve

    Returns:
        Dictionary with sale details including items and payments, or None if not found

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            sale = db.query(Sale).filter(Sale.id == sale_id).first()
            if not sale:
                logger.warning(f"Sale ID {sale_id} not found")
                return None

            # Get customer
            customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()

            # Build sale dict
            sale_dict = {
                'id': sale.id,
                'customer_id': sale.customer_id,
                'customer_name': customer.name if customer else 'Unknown',
                'sale_date': sale.sale_date,
                'subtotal': float(sale.subtotal),
                'tax_amount': float(sale.tax_amount),
                'discount_amount': float(sale.discount_amount),
                'total': float(sale.total),
                'payment_method': sale.payment_method,
                'payment_status': sale.payment_status,
                'notes': sale.notes,
                'status': sale.status,
                'items': [],
                'payments': []
            }

            # Get items
            for item in sale.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                sale_dict['items'].append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name if product else 'Unknown',
                    'product_sku': product.sku if product else None,
                    'quantity': float(item.quantity),
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal),
                    'discount': float(item.discount),
                    'total': float(item.total)
                })

            # Get payments
            for payment in sale.payments:
                sale_dict['payments'].append({
                    'id': payment.id,
                    'payment_date': payment.payment_date,
                    'amount': float(payment.amount),
                    'payment_method': payment.payment_method,
                    'reference': payment.reference,
                    'notes': payment.notes
                })

            # Calculate remaining balance
            total_paid = sum(p['amount'] for p in sale_dict['payments'])
            sale_dict['amount_paid'] = total_paid
            sale_dict['balance_due'] = sale_dict['total'] - total_paid

            logger.info(f"Retrieved sale ID {sale_id}")
            return sale_dict

    except Exception as e:
        logger.error(f"Failed to retrieve sale ID {sale_id}: {e}", exc_info=True)
        raise


def list_sales(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Sale]:
    """List sales with optional filters.

    Args:
        start_date: Filter sales from this date onwards (optional)
        end_date: Filter sales up to this date (optional)
        customer_id: Filter by customer ID (optional)
        status: Filter by status (optional)

    Returns:
        List of Sale objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Sale)

            if start_date:
                query = query.filter(Sale.sale_date >= start_date)
            if end_date:
                query = query.filter(Sale.sale_date <= end_date)
            if customer_id:
                query = query.filter(Sale.customer_id == customer_id)
            if status:
                query = query.filter(Sale.status == status)

            sales = query.order_by(Sale.sale_date.desc()).all()
            logger.info(f"Retrieved {len(sales)} sales")
            return sales

    except Exception as e:
        logger.error(f"Failed to list sales: {e}", exc_info=True)
        raise


def cancel_sale(sale_id: int, reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Cancel a sale and restore stock.

    Args:
        sale_id: ID of the sale to cancel
        reason: Reason for cancellation (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            sale = db.query(Sale).filter(Sale.id == sale_id).first()
            if not sale:
                return False, f"Sale ID {sale_id} not found"

            if sale.status == 'cancelled':
                return False, "Sale is already cancelled"

            # Restore stock for all items
            for item in sale.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock += float(item.quantity)

            # Update sale status
            sale.status = 'cancelled'
            sale.payment_status = 'cancelled'
            sale.notes = f"CANCELLED: {reason or 'No reason provided'}"

            # Update customer balance if credit sale
            if sale.payment_method == 'credit':
                customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
                if customer:
                    customer.balance -= float(sale.total)

            db.commit()
            logger.info(f"Cancelled sale ID {sale_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to cancel sale ID {sale_id}: {e}", exc_info=True)
        return False, "An error occurred while cancelling sale"


def add_payment(
    sale_id: int,
    amount: float,
    payment_method: str,
    reference: Optional[str] = None,
    notes: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Add a payment to a sale (for installment payments).

    Args:
        sale_id: ID of the sale
        amount: Payment amount
        payment_method: Payment method (cash, transfer, card)
        reference: Reference number (optional)
        notes: Additional notes (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    # Validate payment method
    is_valid, error = validate_payment_method(payment_method)
    if not is_valid:
        return False, error

    # Validate amount
    is_valid, error = validate_positive_number(amount, "Payment amount")
    if not is_valid:
        return False, error

    try:
        with get_db_session() as db:
            sale = db.query(Sale).filter(Sale.id == sale_id).first()
            if not sale:
                return False, f"Sale ID {sale_id} not found"

            if sale.status == 'cancelled':
                return False, "Cannot add payment to cancelled sale"

            # Calculate total paid so far
            total_paid = sum(p.amount for p in sale.payments)
            remaining_balance = float(sale.total) - total_paid

            if amount > remaining_balance + 0.01:  # Small tolerance for floating point
                return False, f"Payment amount exceeds remaining balance of {remaining_balance:.2f}"

            # Create payment
            payment = Payment(
                sale_id=sale_id,
                amount=float(amount),
                payment_method=payment_method.lower(),
                reference=reference,
                notes=notes
            )
            db.add(payment)

            # Update payment status if fully paid
            new_total_paid = total_paid + float(amount)
            if new_total_paid >= float(sale.total) - 0.01:  # Small tolerance
                sale.payment_status = 'paid'

            # Reduce customer balance for credit sales
            if sale.payment_method == 'credit':
                customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
                if customer:
                    customer.balance -= float(amount)

            db.commit()
            logger.info(f"Added payment of {amount} to sale ID {sale_id}")
            return True, None

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to add payment to sale ID {sale_id}: {e}", exc_info=True)
        return False, "An error occurred while adding payment"


def validate_positive_number(value: float, field_name: str = "Value") -> Tuple[bool, Optional[str]]:
    """Validate that a number is positive (greater than zero).

    Args:
        value: The number to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        num_value = float(value)
        if num_value <= 0:
            return False, f"{field_name} must be greater than zero"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def get_sales_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get sales summary for a period.

    Args:
        start_date: Start date of period
        end_date: End date of period

    Returns:
        Dictionary with sales summary statistics

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            sales = db.query(Sale).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            total_amount = sum(float(s.total) for s in sales)
            total_discount = sum(float(s.discount_amount) for s in sales)
            total_tax = sum(float(s.tax_amount) for s in sales)

            return {
                'total_sales': len(sales),
                'total_amount': float(total_amount),
                'total_discount': float(total_discount),
                'total_tax': float(total_tax),
                'average_sale': float(total_amount / len(sales)) if sales else 0
            }

    except Exception as e:
        logger.error(f"Failed to get sales summary: {e}", exc_info=True)
        raise
