"""PDF report generation module for ERP Paraguay.

This module provides functions for generating various PDF reports and invoices.
"""
import logging
from datetime import datetime
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from app.reports.pdf_helpers import (
    get_company_info,
    format_currency,
    format_date,
    get_standard_styles,
    create_pdf_table,
    create_pdf_header,
    create_pdf_footer,
    draw_invoice_header,
    draw_invoice_customer,
    safe_text
)
from app.services.sales_management_service import get_sale_by_id
from app.settings import TaxSettings

logger = logging.getLogger(__name__)


def generate_pdf(path: str = "report.pdf") -> None:
    """Generate a sample PDF report (legacy function).

    Args:
        path: Output file path (default: report.pdf)
    """
    c = canvas.Canvas(path)
    c.drawString(100, 750, "ERP Paraguay Demo")
    c.save()


def generate_invoice(path: str, sale_id: int) -> None:
    """Generate a professional invoice PDF.

    Args:
        path: Output file path
        sale_id: ID of the sale to generate invoice for

    Raises:
        Exception: If sale not found or PDF generation fails
    """
    try:
        # Get sale data
        sale = get_sale_by_id(sale_id)
        if not sale:
            raise ValueError(f"Sale ID {sale_id} not found")

        # Create PDF
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        # Container for PDF elements
        elements = []
        styles = get_standard_styles()

        # Company info
        company = get_company_info()
        elements.append(Paragraph(company['name'], styles['CompanyHeader']))
        elements.append(Spacer(1, 12))

        company_details = f"""
        {company['address']}<br/>
        Tel: {company['phone']} | Email: {company['email']}<br/>
        RUC: {company['tax_id']}
        """
        elements.append(Paragraph(company_details, styles['Normal']))
        elements.append(Spacer(1, 12))

        # Invoice title and info
        invoice_info = f"""
        <b>FACTURA N°: {sale['id']}</b><br/>
        Fecha: {format_date(sale['sale_date'])}<br/>
        Estado: {sale['status'].upper()}
        """
        elements.append(Paragraph(invoice_info, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Customer info
        customer_header = Paragraph("<b>CLIENTE:</b>", styles['Normal'])
        elements.append(customer_header)

        customer_info = f"""
        {safe_text(sale['customer_name'])}<br/>
        """
        if sale.get('customer_tax_id'):
            customer_info += f"RUC/CI: {sale['customer_tax_id']}<br/>"

        elements.append(Paragraph(customer_info, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Items table
        headers = ['Producto', 'Cant.', 'Precio Unit.', 'Descuento', 'Total']
        item_data = []
        for item in sale['items']:
            item_data.append([
                safe_text(item['product_name']),
                f"{item['quantity']:.2f}",
                f"{format_currency(item['unit_price'])}",
                f"{format_currency(item['discount'])}",
                f"{format_currency(item['total'])}"
            ])

        items_table = create_pdf_table(
            item_data,
            headers,
            column_widths=[3.5*inch, 0.8*inch, 1*inch, 1*inch, 1*inch],
            align_data='RIGHT'
        )
        # Align first column (product name) to left
        items_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT')]))
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        # Totals section
        totals_data = [
            ['Subtotal:', format_currency(sale['subtotal'])],
            [f'{TaxSettings.get_display_string()}:', format_currency(sale['tax_amount'])],
            ['Descuento:', format_currency(sale['discount_amount'])],
            ['<b>TOTAL:</b>', f"<b>{format_currency(sale['total'])}</b>"]
        ]

        totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 3), (-1, 3), 12),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#1a5276')),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.HexColor('#1a5276')),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 20))

        # Payment information
        payment_info = f"""
        <b>Método de Pago:</b> {sale['payment_method'].upper()}<br/>
        <b>Estado de Pago:</b> {sale['payment_status'].upper()}
        """
        elements.append(Paragraph(payment_info, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Payments made
        if sale['payments']:
            elements.append(Paragraph("<b>PAGOS REALIZADOS:</b>", styles['Normal']))
            for payment in sale['payments']:
                payment_text = f"""
                • {format_currency(payment['amount'])} - {payment['payment_method'].upper()}
                  ({format_date(payment['payment_date'])})
                """
                elements.append(Paragraph(payment_text, styles['Normal']))

        # Balance due
        if sale.get('balance_due', 0) > 0:
            elements.append(Spacer(1, 12))
            balance_text = f"<b>Saldo Pendiente: {format_currency(sale['balance_due'])}</b>"
            elements.append(Paragraph(balance_text, styles['Normal']))
            elements[-1].style = ParagraphStyle(
                'BalanceDue',
                parent=styles['Normal'],
                textColor=colors.red,
                fontSize=12
            )

        # Terms and conditions
        elements.append(PageBreak())
        elements.append(Spacer(1, inch))
        terms = """
        <b>TÉRMINOS Y CONDICIONES:</b><br/><br/>
        1. Los precios están en Guaraníes.<br/>
        2. El pago debe realizarse según las condiciones acordadas.<br/>
        3. Los productos una vez vendidos no tienen devolución.<br/>
        4. Para cualquier consulta, contactar al número arriba indicado.<br/><br/>
        <i>¡Gracias por su preferencia!</i>
        """
        elements.append(Paragraph(terms, styles['Normal']))

        # Build PDF
        doc.build(elements)

        logger.info(f"Invoice generated: {path} for sale {sale_id}")

    except Exception as e:
        logger.error(f"Failed to generate invoice for sale {sale_id}: {e}", exc_info=True)
        raise


def generate_sales_report(path: str, start_date: datetime, end_date: datetime) -> None:
    """Generate a sales summary report for a period.

    Args:
        path: Output file path
        start_date: Start of period
        end_date: End of period

    Raises:
        Exception: If report generation fails
    """
    try:
        from app.services.reports_service import get_sales_summary, get_top_products, get_top_customers

        # Get data
        summary = get_sales_summary(start_date, end_date)
        top_products = get_top_products(start_date, end_date, limit=10)
        top_customers = get_top_customers(start_date, end_date, limit=10)

        # Create PDF
        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = []
        styles = get_standard_styles()

        # Title
        elements.append(Paragraph("REPORTE DE VENTAS", styles['InvoiceTitle']))
        elements.append(Spacer(1, 12))

        # Period
        period_text = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Summary section
        elements.append(Paragraph("<b>RESUMEN GENERAL</b>", styles['Normal']))
        elements.append(Spacer(1, 12))

        summary_data = [
            ['Total de Ventas:', str(summary['total_sales'])],
            ['Monto Total:', format_currency(summary['total_amount'])],
            ['Descuento Total:', format_currency(summary['total_discount'])],
            ['IVA Total:', format_currency(summary['total_tax'])],
            ['Promedio por Venta:', format_currency(summary['average_sale'])],
            ['Total de Ítems:', str(summary['total_items'])]
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.gray),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Top products
        elements.append(Paragraph("<b>TOP 10 PRODUCTOS</b>", styles['Normal']))
        elements.append(Spacer(1, 12))

        if top_products:
            headers = ['Producto', 'SKU', 'Cantidad', 'Revenue']
            product_data = []
            for product in top_products:
                product_data.append([
                    safe_text(product['product_name']),
                    safe_text(product.get('product_sku') or '-'),
                    f"{product['quantity']:.2f}",
                    format_currency(product['revenue'])
                ])

            products_table = create_pdf_table(
                product_data,
                headers,
                column_widths=[2.5*inch, 1*inch, 1*inch, 1.5*inch],
                align_data='RIGHT'
            )
            products_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT')]))
            elements.append(products_table)

        elements.append(Spacer(1, 20))

        # Top customers
        elements.append(Paragraph("<b>TOP 10 CLIENTES</b>", styles['Normal']))
        elements.append(Spacer(1, 12))

        if top_customers:
            headers = ['Cliente', 'Compras', 'Total']
            customer_data = []
            for customer in top_customers:
                customer_data.append([
                    safe_text(customer['customer_name']),
                    str(customer['sale_count']),
                    format_currency(customer['total_purchases'])
                ])

            customers_table = create_pdf_table(
                customer_data,
                headers,
                column_widths=[3*inch, 1*inch, 1.5*inch],
                align_data='RIGHT'
            )
            customers_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT')]))
            elements.append(customers_table)

        # Build PDF
        doc.build(elements)

        logger.info(f"Sales report generated: {path}")

    except Exception as e:
        logger.error(f"Failed to generate sales report: {e}", exc_info=True)
        raise


def generate_inventory_report(path: str) -> None:
    """Generate an inventory status report.

    Args:
        path: Output file path

    Raises:
        Exception: If report generation fails
    """
    try:
        from app.services.reports_service import get_inventory_report

        # Get data
        inventory = get_inventory_report()

        # Create PDF
        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = []
        styles = get_standard_styles()

        # Title
        elements.append(Paragraph("REPORTE DE INVENTARIO", styles['InvoiceTitle']))
        elements.append(Spacer(1, 12))

        # Date
        date_text = f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Summary
        total_products = len(inventory)
        total_value = sum(item['retail_value'] for item in inventory)
        total_cost = sum(item['cost_value'] for item in inventory if item['cost_value'])
        total_profit = total_value - total_cost

        summary_data = [
            ['Total de Productos:', str(total_products)],
            ['Valor de Retail Total:', format_currency(total_value)],
            ['Valor de Costo Total:', format_currency(total_cost)],
            ['Ganancia Potencial:', format_currency(total_profit)]
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Inventory table
        headers = ['Producto', 'SKU', 'Categoría', 'Stock', 'Precio', 'Valor Total']
        inventory_data = []
        for item in inventory:
            inventory_data.append([
                safe_text(item['product_name']),
                safe_text(item.get('product_sku') or '-'),
                safe_text(item.get('category') or '-'),
                f"{item['stock']:.2f}",
                format_currency(item['price']),
                format_currency(item['retail_value'])
            ])

        inventory_table = create_pdf_table(
            inventory_data,
            headers,
            column_widths=[2.5*inch, 0.8*inch, 1*inch, 0.7*inch, 0.8*inch, 1*inch],
            align_data='RIGHT'
        )
        inventory_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT')]))
        elements.append(inventory_table)

        # Build PDF
        doc.build(elements)

        logger.info(f"Inventory report generated: {path}")

    except Exception as e:
        logger.error(f"Failed to generate inventory report: {e}", exc_info=True)
        raise


def generate_customer_statement(path: str, customer_id: int, start_date: datetime, end_date: datetime) -> None:
    """Generate a customer account statement.

    Args:
        path: Output file path
        customer_id: Customer ID
        start_date: Start of period
        end_date: End of period

    Raises:
        Exception: If report generation fails
    """
    try:
        from app.services.reports_service import get_customer_statement

        # Get data
        statement = get_customer_statement(customer_id, start_date, end_date)

        # Create PDF
        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = []
        styles = get_standard_styles()

        # Title
        elements.append(Paragraph("ESTADO DE CUENTA", styles['InvoiceTitle']))
        elements.append(Spacer(1, 12))

        # Period
        period_text = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Customer info
        elements.append(Paragraph("<b>CLIENTE:</b>", styles['Normal']))
        customer_text = f"""
        {safe_text(statement['customer_name'])}<br/>
        """
        if statement.get('customer_email'):
            customer_text += f"Email: {statement['customer_email']}<br/>"
        if statement.get('customer_phone'):
            customer_text += f"Tel: {statement['customer_phone']}<br/>"
        if statement.get('customer_tax_id'):
            customer_text += f"RUC/CI: {statement['customer_tax_id']}"

        elements.append(Paragraph(customer_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Balance summary
        balance_data = [
            ['Saldo Anterior:', format_currency(statement['current_balance'] - statement.get('net_change', 0))],
            ['Compras del Período:', format_currency(statement['total_purchases'])],
            ['Pagos del Período:', format_currency(statement['total_payments'])],
            ['<b>Saldo Actual:</b>', f"<b>{format_currency(statement['current_balance'])}</b>"]
        ]

        balance_table = Table(balance_data, colWidths=[3*inch, 2*inch])
        balance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#1a5276')),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.HexColor('#1a5276')),
        ]))
        elements.append(balance_table)
        elements.append(Spacer(1, 20))

        # Sales/Transactions
        if statement['sales']:
            elements.append(Paragraph("<b>TRANSACCIONES:</b>", styles['Normal']))
            elements.append(Spacer(1, 12))

            headers = ['Fecha', 'ID', 'Tipo', 'Monto']
            transaction_data = []
            for sale in statement['sales']:
                transaction_data.append([
                    format_date(sale['date']),
                    str(sale['id']),
                    'Venta',
                    format_currency(sale['total'])
                ])

            for payment in statement['payments']:
                transaction_data.append([
                    format_date(payment['date']),
                    str(payment['id']),
                    'Pago',
                    f"-{format_currency(payment['amount'])}"
                ])

            transactions_table = create_pdf_table(
                transaction_data,
                headers,
                column_widths=[1.5*inch, 0.8*inch, 1*inch, 1.5*inch],
                align_data='RIGHT'
            )
            transactions_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT')]))
            elements.append(transactions_table)

        # Build PDF
        doc.build(elements)

        logger.info(f"Customer statement generated: {path}")

    except Exception as e:
        logger.error(f"Failed to generate customer statement: {e}", exc_info=True)
        raise
