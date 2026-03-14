"""Reports service module for ERP Paraguay.

This module provides business logic for generating various reports.
All queries use eager loading to prevent N+1 query problems.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from app.database.db import get_db_session
from app.database.models import Sale, SaleItem, Product, Customer, Payment, Category

logger = logging.getLogger(__name__)


def get_sales_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get sales summary statistics for a period.

    Uses eager loading to prevent N+1 queries when accessing sale items.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with sales statistics

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use selectinload for items relationship to prevent N+1 queries
            sales = db.query(Sale).options(
                selectinload(Sale.items)
            ).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            if not sales:
                return {
                    'total_sales': 0,
                    'total_amount': 0.0,
                    'total_discount': 0.0,
                    'total_tax': 0.0,
                    'average_sale': 0.0,
                    'total_items': 0,
                    'payment_methods': {}
                }

            total_amount = sum(float(s.total) for s in sales)
            total_discount = sum(float(s.discount_amount) for s in sales)
            total_tax = sum(float(s.tax_amount) for s in sales)
            total_items = sum(len(s.items) for s in sales)

            # Count by payment method
            payment_methods = {}
            for sale in sales:
                pm = sale.payment_method
                payment_methods[pm] = payment_methods.get(pm, 0) + 1

            return {
                'total_sales': len(sales),
                'total_amount': total_amount,
                'total_discount': total_discount,
                'total_tax': total_tax,
                'average_sale': total_amount / len(sales),
                'total_items': total_items,
                'payment_methods': payment_methods
            }

    except Exception as e:
        logger.error(f"Failed to get sales summary: {e}", exc_info=True)
        raise


def get_profit_margin_report(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get profit margin by product for a period.

    Uses eager loading to prevent N+1 queries when accessing products.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        List of dictionaries with product profit info

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use joinedload to eagerly load products with sale items
            # This prevents N+1 queries when accessing item.product
            sale_items = db.query(SaleItem).options(
                joinedload(SaleItem.product)
            ).join(Sale).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            # Group by product using the already-loaded product relationship
            product_stats = {}
            for item in sale_items:
                pid = item.product_id
                if pid not in product_stats:
                    product = item.product  # Already loaded via joinedload
                    product_stats[pid] = {
                        'product_id': pid,
                        'product_name': product.name if product else 'Unknown',
                        'product_sku': product.sku if product else None,
                        'quantity_sold': 0,
                        'revenue': 0.0,
                        'cost': 0.0,
                        'profit': 0.0
                    }

                qty = float(item.quantity)
                revenue = float(item.total)

                # Calculate cost using the already-loaded product
                product = item.product
                cost_price = float(product.cost_price) if product and product.cost_price else 0.0
                cost = qty * cost_price

                product_stats[pid]['quantity_sold'] += qty
                product_stats[pid]['revenue'] += revenue
                product_stats[pid]['cost'] += cost
                product_stats[pid]['profit'] += (revenue - cost)

            # Calculate margin percentage
            for stats in product_stats.values():
                if stats['revenue'] > 0:
                    stats['margin_percent'] = (stats['profit'] / stats['revenue']) * 100
                else:
                    stats['margin_percent'] = 0.0

            return list(product_stats.values())

    except Exception as e:
        logger.error(f"Failed to get profit margin report: {e}", exc_info=True)
        raise


def get_customer_statement(customer_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get customer account statement for a period.

    Args:
        customer_id: Customer ID
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with customer statement

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer ID {customer_id} not found")

            # Get sales in period
            sales = db.query(Sale).filter(
                Sale.customer_id == customer_id,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date
            ).all()

            # Get payments in period
            payments = db.query(Payment).join(Sale).filter(
                Sale.customer_id == customer_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).all()

            # Calculate totals
            total_purchases = sum(float(s.total) for s in sales if s.payment_method == 'credit')
            total_payments = sum(float(p.amount) for p in payments)

            return {
                'customer_id': customer.id,
                'customer_name': customer.name,
                'customer_email': customer.email,
                'customer_phone': customer.phone,
                'customer_address': customer.address,
                'customer_tax_id': customer.tax_id,
                'current_balance': float(customer.balance),
                'period_start': start_date,
                'period_end': end_date,
                'sales': [{
                    'id': s.id,
                    'date': s.sale_date,
                    'total': float(s.total),
                    'payment_method': s.payment_method,
                    'status': s.status
                } for s in sales],
                'payments': [{
                    'id': p.id,
                    'date': p.payment_date,
                    'amount': float(p.amount),
                    'method': p.payment_method,
                    'reference': p.reference
                } for p in payments],
                'total_purchases': total_purchases,
                'total_payments': total_payments,
                'net_change': total_purchases - total_payments
            }

    except Exception as e:
        logger.error(f"Failed to get customer statement: {e}", exc_info=True)
        raise


def get_inventory_report() -> List[Dict[str, Any]]:
    """Get current inventory status report.

    Uses eager loading to prevent N+1 queries when accessing categories.

    Returns:
        List of dictionaries with product inventory info

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use joinedload to eagerly load categories
            products = db.query(Product).options(
                joinedload(Product.category)
            ).filter(
                Product.is_active == True
            ).all()

            report = []
            for product in products:
                # Calculate inventory value
                retail_value = float(product.price) * float(product.stock)
                cost_value = float(product.cost_price) * float(product.stock) if product.cost_price else 0.0

                report.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_sku': product.sku,
                    'category': product.category.name if product.category else None,
                    'stock': float(product.stock),
                    'reorder_point': float(product.reorder_point),
                    'needs_reorder': float(product.stock) <= float(product.reorder_point),
                    'price': float(product.price),
                    'cost_price': float(product.cost_price) if product.cost_price else None,
                    'retail_value': retail_value,
                    'cost_value': cost_value,
                    'potential_profit': retail_value - cost_value
                })

            return report

    except Exception as e:
        logger.error(f"Failed to get inventory report: {e}", exc_info=True)
        raise


def get_top_products(start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top selling products by quantity or revenue.

    Uses eager loading to prevent N+1 queries when accessing products.

    Args:
        start_date: Start of period
        end_date: End of period
        limit: Maximum number of products to return

    Returns:
        List of top products

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use joinedload to eagerly load products
            sale_items = db.query(SaleItem).options(
                joinedload(SaleItem.product)
            ).join(Sale).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            # Aggregate by product using already-loaded products
            product_sales = {}
            for item in sale_items:
                pid = item.product_id
                if pid not in product_sales:
                    product = item.product  # Already loaded
                    product_sales[pid] = {
                        'product_id': pid,
                        'product_name': product.name if product else 'Unknown',
                        'product_sku': product.sku if product else None,
                        'quantity': 0.0,
                        'revenue': 0.0
                    }

                product_sales[pid]['quantity'] += float(item.quantity)
                product_sales[pid]['revenue'] += float(item.total)

            # Sort by revenue and return top N
            sorted_products = sorted(
                product_sales.values(),
                key=lambda x: x['revenue'],
                reverse=True
            )[:limit]

            return sorted_products

    except Exception as e:
        logger.error(f"Failed to get top products: {e}", exc_info=True)
        raise


def get_top_customers(start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top customers by purchase amount.

    Uses eager loading and aggregation to prevent N+1 queries.

    Args:
        start_date: Start of period
        end_date: End of period
        limit: Maximum number of customers to return

    Returns:
        List of top customers

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use joinedload to eagerly load customers and aggregate in database
            sales = db.query(Sale).options(
                joinedload(Sale.customer)
            ).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            # Aggregate by customer using already-loaded customers
            customer_sales = {}
            for sale in sales:
                cid = sale.customer_id
                if cid not in customer_sales:
                    customer = sale.customer  # Already loaded
                    customer_sales[cid] = {
                        'customer_id': cid,
                        'customer_name': customer.name if customer else 'Unknown',
                        'total_purchases': 0.0,
                        'sale_count': 0
                    }

                customer_sales[cid]['total_purchases'] += float(sale.total)
                customer_sales[cid]['sale_count'] += 1

            # Sort by total purchases and return top N
            sorted_customers = sorted(
                customer_sales.values(),
                key=lambda x: x['total_purchases'],
                reverse=True
            )[:limit]

            return sorted_customers

    except Exception as e:
        logger.error(f"Failed to get top customers: {e}", exc_info=True)
        raise


def get_daily_sales(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get daily sales breakdown.

    Uses eager loading to prevent N+1 queries when accessing sale items.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        List of daily sales summaries

    Raises:
        Exception: If database query fails
    """
    try:
        with get_db_session() as db:
            # Use selectinload for items relationship
            sales = db.query(Sale).options(
                selectinload(Sale.items)
            ).filter(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == 'completed'
            ).all()

            # Group by date
            daily_sales = {}
            for sale in sales:
                date_key = sale.sale_date.date()
                if date_key not in daily_sales:
                    daily_sales[date_key] = {
                        'date': date_key,
                        'total_sales': 0,
                        'total_amount': 0.0,
                        'total_items': 0
                    }

                daily_sales[date_key]['total_sales'] += 1
                daily_sales[date_key]['total_amount'] += float(sale.total)
                daily_sales[date_key]['total_items'] += len(sale.items)  # Already loaded

            # Convert to list and sort by date
            result = [
                {
                    'date': str(data['date']),
                    'total_sales': data['total_sales'],
                    'total_amount': data['total_amount'],
                    'total_items': data['total_items']
                }
                for data in sorted(daily_sales.values(), key=lambda x: x['date'])
            ]

            return result

    except Exception as e:
        logger.error(f"Failed to get daily sales: {e}", exc_info=True)
        raise
