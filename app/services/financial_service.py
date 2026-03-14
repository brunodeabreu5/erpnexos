"""Financial service module for ERP Paraguay.

This module provides business logic for financial management operations.
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.database.db import get_db_session
from app.database.models import Expense, Sale
from app.validators import (
    validate_expense_category,
    validate_payment_method_for_expense,
    validate_expense_amount,
    validate_required_string,
    validate_non_negative_number
)

logger = logging.getLogger(__name__)

# Expense category display names (localized)
EXPENSE_CATEGORIES = {
    'rent': 'Aluguel',
    'utilities': 'Água/Luz/Telefone',
    'salaries': 'Salários',
    'taxes': 'Impostos',
    'materials': 'Materiais',
    'marketing': 'Marketing',
    'maintenance': 'Manutenção',
    'shipping': 'Frete/Transporte',
    'other': 'Outros'
}


def create_expense(
    category: str,
    amount: float,
    description: str,
    expense_date: datetime,
    payment_method: Optional[str] = None,
    reference: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Expense]]:
    """Create a new expense in the database.

    Args:
        category: Expense category (required)
        amount: Expense amount (required, must be positive)
        description: Description of the expense (required)
        expense_date: Date of the expense (required)
        payment_method: Payment method (optional)
        reference: Reference number (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], expense: Optional[Expense])
    """
    # Validate inputs
    is_valid, error = validate_expense_category(category)
    if not is_valid:
        return False, error, None

    is_valid, error = validate_expense_amount(amount)
    if not is_valid:
        return False, error, None

    is_valid, error = validate_required_string(description, "Description", 500)
    if not is_valid:
        return False, error, None

    if payment_method:
        is_valid, error = validate_payment_method_for_expense(payment_method)
        if not is_valid:
            return False, error, None

    try:
        with get_db_session() as db:
            expense = Expense(
                category=category.strip().lower(),
                amount=float(amount),
                description=description.strip(),
                expense_date=expense_date,
                payment_method=payment_method.strip().lower() if payment_method else None,
                reference=reference.strip() if reference else None
            )
            db.add(expense)
            db.commit()
            db.refresh(expense)
            logger.info(f"Created expense: {expense}")
            return True, None, expense

    except Exception as e:
        logger.error(f"Failed to create expense: {e}", exc_info=True)
        return False, "An error occurred while creating expense", None


def list_expenses(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None
) -> List[Expense]:
    """Retrieve expenses from the database with optional filters.

    Args:
        start_date: Filter expenses from this date onwards (optional)
        end_date: Filter expenses up to this date (optional)
        category: Filter by category (optional)

    Returns:
        List of Expense objects

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            query = db.query(Expense)

            if start_date:
                query = query.filter(Expense.expense_date >= start_date)
            if end_date:
                query = query.filter(Expense.expense_date <= end_date)
            if category:
                query = query.filter(Expense.category == category.lower())

            expenses = query.order_by(Expense.expense_date.desc()).all()
            logger.info(f"Retrieved {len(expenses)} expenses")
            return expenses

    except Exception as e:
        logger.error(f"Failed to retrieve expenses: {e}", exc_info=True)
        raise


def get_expense_by_id(expense_id: int) -> Optional[Expense]:
    """Retrieve a single expense by its ID.

    Args:
        expense_id: The ID of the expense to retrieve

    Returns:
        Expense object if found, None otherwise

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if expense:
                logger.info(f"Retrieved expense ID {expense_id}")
            else:
                logger.warning(f"Expense ID {expense_id} not found")
            return expense

    except Exception as e:
        logger.error(f"Failed to retrieve expense ID {expense_id}: {e}", exc_info=True)
        raise


def update_expense(
    expense_id: int,
    category: Optional[str] = None,
    amount: Optional[float] = None,
    description: Optional[str] = None,
    expense_date: Optional[datetime] = None,
    payment_method: Optional[str] = None,
    reference: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Expense]]:
    """Update an existing expense.

    Args:
        expense_id: ID of the expense to update
        category: New category (optional)
        amount: New amount (optional)
        description: New description (optional)
        expense_date: New expense date (optional)
        payment_method: New payment method (optional)
        reference: New reference (optional)

    Returns:
        Tuple of (success: bool, error_message: Optional[str], expense: Optional[Expense])
    """
    try:
        with get_db_session() as db:
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if not expense:
                return False, f"Expense ID {expense_id} not found", None

            # Validate and update category if provided
            if category is not None:
                is_valid, error = validate_expense_category(category)
                if not is_valid:
                    return False, error, None
                expense.category = category.strip().lower()

            # Validate and update amount if provided
            if amount is not None:
                is_valid, error = validate_expense_amount(amount)
                if not is_valid:
                    return False, error, None
                expense.amount = float(amount)

            # Update description if provided
            if description is not None:
                is_valid, error = validate_required_string(description, "Description", 500)
                if not is_valid:
                    return False, error, None
                expense.description = description.strip()

            # Update expense_date if provided
            if expense_date is not None:
                expense.expense_date = expense_date

            # Validate and update payment_method if provided
            if payment_method is not None:
                if payment_method:  # Non-empty
                    is_valid, error = validate_payment_method_for_expense(payment_method)
                    if not is_valid:
                        return False, error, None
                    expense.payment_method = payment_method.strip().lower()
                else:
                    expense.payment_method = None

            # Update reference if provided
            if reference is not None:
                expense.reference = reference.strip() if reference else None

            db.commit()
            db.refresh(expense)
            logger.info(f"Updated expense ID {expense_id}: {expense}")
            return True, None, expense

    except Exception as e:
        logger.error(f"Failed to update expense ID {expense_id}: {e}", exc_info=True)
        return False, "An error occurred while updating expense", None


def delete_expense(expense_id: int) -> Tuple[bool, Optional[str]]:
    """Delete an expense from the database.

    Args:
        expense_id: ID of the expense to delete

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        with get_db_session() as db:
            expense = db.query(Expense).filter(Expense.id == expense_id).first()
            if not expense:
                return False, f"Expense ID {expense_id} not found"

            db.delete(expense)
            db.commit()
            logger.info(f"Deleted expense ID {expense_id}")
            return True, None

    except Exception as e:
        logger.error(f"Failed to delete expense ID {expense_id}: {e}", exc_info=True)
        return False, "An error occurred while deleting expense"


def get_profit_loss_statement(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate a Profit & Loss statement for a period.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with P&L data including revenue, expenses, profit

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Get total revenue from sales
            sales = db.query(Sale).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            total_revenue = sum(float(s.total) for s in sales)
            cost_of_goods_sold = sum(
                sum(float(item.quantity) * float(item.product.cost_price or 0))
                for s in sales
                for item in s.items
                if item.product
            )
            gross_profit = total_revenue - cost_of_goods_sold

            # Get total expenses
            expenses = db.query(Expense).filter(
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            ).all()

            total_expenses = sum(float(e.amount) for e in expenses)

            # Calculate operating profit and net profit
            operating_profit = gross_profit - total_expenses
            net_profit = operating_profit

            # Get expenses by category
            expenses_by_category = {}
            for expense in expenses:
                category_display = EXPENSE_CATEGORIES.get(expense.category, expense.category)
                if category_display not in expenses_by_category:
                    expenses_by_category[category_display] = 0.0
                expenses_by_category[category_display] += float(expense.amount)

            return {
                'period_start': start_date,
                'period_end': end_date,
                'revenue': {
                    'total': total_revenue,
                    'sales_count': len(sales)
                },
                'cost_of_goods_sold': cost_of_goods_sold,
                'gross_profit': gross_profit,
                'expenses': {
                    'total': total_expenses,
                    'by_category': expenses_by_category
                },
                'operating_profit': operating_profit,
                'net_profit': net_profit,
                'profit_margin': (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            }

    except Exception as e:
        logger.error(f"Failed to generate P&L statement: {e}", exc_info=True)
        raise


def get_expenses_by_category(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get expense breakdown by category for a period.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with expense totals by category

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            expenses = db.query(Expense).filter(
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            ).all()

            # Group by category
            category_totals = {}
            for expense in expenses:
                category_display = EXPENSE_CATEGORIES.get(expense.category, expense.category)
                if category_display not in category_totals:
                    category_totals[category_display] = {
                        'amount': 0.0,
                        'count': 0
                    }
                category_totals[category_display]['amount'] += float(expense.amount)
                category_totals[category_display]['count'] += 1

            # Calculate total
            total_amount = sum(data['amount'] for data in category_totals.values())

            # Calculate percentages
            for category_data in category_totals.values():
                category_data['percentage'] = (
                    (category_data['amount'] / total_amount * 100) if total_amount > 0 else 0
                )

            return {
                'period_start': start_date,
                'period_end': end_date,
                'total_expenses': total_amount,
                'by_category': category_totals
            }

    except Exception as e:
        logger.error(f"Failed to get expenses by category: {e}", exc_info=True)
        raise


def get_financial_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get a comprehensive financial summary for a period.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with financial summary including cash flow

    Raises:
        Exception: If database query fails
    """
    try:
        # Get P&L statement
        pl_statement = get_profit_loss_statement(start_date, end_date)

        # Calculate cash flow (simplified - cash sales vs cash expenses)
        with get_db_session() as db:
            # Cash received from sales
            cash_sales = db.query(Sale).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed',
                Sale.payment_method.in_(['cash', 'card', 'transfer'])
            ).all()

            cash_in = sum(float(s.total) for s in cash_sales)

            # Cash paid for expenses
            cash_expenses = db.query(Expense).filter(
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
                Expense.payment_method.in_(['cash', 'card', 'transfer', 'pix'])
            ).all()

            cash_out = sum(float(e.amount) for e in cash_expenses)

            net_cash_flow = cash_in - cash_out

            return {
                **pl_statement,
                'cash_flow': {
                    'cash_in': cash_in,
                    'cash_out': cash_out,
                    'net_flow': net_cash_flow
                }
            }

    except Exception as e:
        logger.error(f"Failed to get financial summary: {e}", exc_info=True)
        raise
