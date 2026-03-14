"""PDF helper functions for ERP Paraguay.

This module provides reusable helper functions for PDF generation.
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os


def get_company_info() -> dict:
    """Get company information for use in invoices and reports.

    Returns:
        Dictionary with company details
    """
    from app.settings import CompanySettings
    return CompanySettings.to_dict()


def format_currency(amount: float) -> str:
    """Format a number as currency string.

    Args:
        amount: The amount to format

    Returns:
        Formatted currency string
    """
    try:
        amount_float = float(amount)
        return f"{amount_float:,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def format_date(date: datetime) -> str:
    """Format a datetime object as string.

    Args:
        date: The datetime to format

    Returns:
        Formatted date string
    """
    if isinstance(date, datetime):
        return date.strftime("%d/%m/%Y %H:%M")
    return str(date)


def get_standard_styles() -> dict:
    """Get standard paragraph styles for PDF documents.

    Returns:
        Dictionary of ParagraphStyle objects
    """
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name='CompanyHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=12,
        alignment=0  # Left
    ))

    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=12,
        alignment=1  # Center
    ))

    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
    ))

    styles.add(ParagraphStyle(
        name='Value',
        parent=styles['Normal'],
        fontSize=10,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1  # Center
    ))

    return styles


def create_pdf_table(data, headers, column_widths=None, align_header='CENTER', align_data='LEFT'):
    """Create a formatted table for PDF.

    Args:
        data: List of lists with table data
        headers: List of header strings
        column_widths: Optional list of column widths
        align_header: Alignment for header row
        align_data: Alignment for data rows

    Returns:
        Formatted Table object
    """
    # Combine headers and data
    table_data = [headers] + data

    # Create table
    table = Table(table_data, colWidths=column_widths)

    # Define table style
    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), align_header),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),

        # Data rows
        ('ALIGN', (0, 1), (-1, -1), align_data),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
    ])

    table.setStyle(style)
    return table


def create_pdf_header(canvas_obj, title, page_width):
    """Draw a standard header on a PDF page.

    Args:
        canvas_obj: ReportLab canvas object
        title: Page title
        page_width: Width of the page
    """
    # Draw horizontal line
    canvas_obj.setStrokeColor(colors.HexColor('#1a5276'))
    canvas_obj.setLineWidth(2)
    canvas_obj.line(50, 780, page_width - 50, 780)

    # Draw title
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.setFillColor(colors.HexColor('#1a5276'))
    canvas_obj.drawString(50, 750, title)

    # Draw date
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.setFillColor(colors.gray)
    canvas_obj.drawRightString(page_width - 50, 750, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


def create_pdf_footer(canvas_obj, page_num, page_width, page_height):
    """Draw a standard footer on a PDF page.

    Args:
        canvas_obj: ReportLab canvas object
        page_num: Current page number
        page_width: Width of the page
        page_height: Height of the page
    """
    # Draw horizontal line
    canvas_obj.setStrokeColor(colors.gray)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(50, 50, page_width - 50, 50)

    # Draw page number
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.gray)
    canvas_obj.drawCenteredString(page_width / 2, 35, f"Página {page_num}")

    # Draw company info
    company = get_company_info()
    footer_text = f"{company['name']} | {company['address']} | Tel: {company['phone']}"
    canvas_obj.drawString(50, 20, footer_text)


def create_pdf_line(canvas_obj, y_position, page_width, color=colors.gray, line_width=1):
    """Draw a horizontal line on the PDF.

    Args:
        canvas_obj: ReportLab canvas object
        y_position: Y coordinate for the line
        page_width: Width of the page
        color: Line color
        line_width: Line thickness
    """
    canvas_obj.setStrokeColor(color)
    canvas_obj.setLineWidth(line_width)
    canvas_obj.line(50, y_position, page_width - 50, y_position)


def draw_invoice_header(canvas_obj, invoice_data, page_width):
    """Draw invoice-specific header information.

    Args:
        canvas_obj: ReportLab canvas object
        invoice_data: Dictionary with invoice details
        page_width: Width of the page
    """
    y_pos = 700

    # Company info
    company = get_company_info()
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.setFillColor(colors.HexColor('#1a5276'))
    canvas_obj.drawString(50, y_pos, company['name'])

    y_pos -= 20
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.black)
    canvas_obj.drawString(50, y_pos, company['address'])
    y_pos -= 15
    canvas_obj.drawString(50, y_pos, f"Tel: {company['phone']} | {company['email']}")
    y_pos -= 15
    canvas_obj.drawString(50, y_pos, f"RUC: {company['tax_id']}")

    # Invoice info on the right
    canvas_obj.drawRightString(page_width - 50, y_pos, f"Factura N°: {invoice_data.get('id', '')}")
    y_pos -= 20
    canvas_obj.drawRightString(page_width - 50, y_pos, f"Fecha: {format_date(invoice_data.get('sale_date', datetime.now()))}")

    return y_pos - 30


def draw_invoice_customer(canvas_obj, customer_data, y_pos):
    """Draw customer information on invoice.

    Args:
        canvas_obj: ReportLab canvas object
        customer_data: Dictionary with customer details
        y_pos: Starting Y position

    Returns:
        New Y position after drawing
    """
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.setFillColor(colors.black)
    canvas_obj.drawString(50, y_pos, "Cliente:")

    y_pos -= 20
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawString(50, y_pos, customer_data.get('customer_name', ''))

    if customer_data.get('customer_tax_id'):
        y_pos -= 15
        canvas_obj.drawString(50, y_pos, f"RUC/CI: {customer_data['customer_tax_id']}")

    if customer_data.get('customer_address'):
        y_pos -= 15
        canvas_obj.drawString(50, y_pos, customer_data['customer_address'])

    if customer_data.get('customer_phone'):
        y_pos -= 15
        canvas_obj.drawString(50, y_pos, f"Tel: {customer_data['customer_phone']}")

    return y_pos - 20


def calculate_page_elements(elements, page_height, margin=100):
    """Calculate how many elements fit on a page.

    Args:
        elements: List of flowable elements
        page_height: Height of the page
        margin: Bottom margin to leave

    Returns:
        Tuple of (elements_for_page, remaining_elements)
    """
    # This is a simplified version
    # A full implementation would calculate actual heights
    max_elements = 25  # Approximate number of table rows per page
    if len(elements) <= max_elements:
        return elements, []
    return elements[:max_elements], elements[max_elements:]


def safe_text(text):
    """Clean text for safe PDF rendering.

    Args:
        text: Text to clean

    Returns:
        Safe text string
    """
    if text is None:
        return ""
    # Remove or replace problematic characters
    return str(text).encode('utf-8', errors='ignore').decode('utf-8')
