"""Application settings for ERP Paraguay.

This module centralizes all configuration settings loaded from environment variables,
providing grouped access to different configuration categories.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CompanySettings:
    """Company information settings used in invoices and reports."""

    # Company basic information
    NAME: str = os.getenv("COMPANY_NAME", "ERP Paraguay")
    ADDRESS: str = os.getenv("COMPANY_ADDRESS", "Dirección de la empresa")
    PHONE: str = os.getenv("COMPANY_PHONE", "+595 21 123 456")
    EMAIL: str = os.getenv("COMPANY_EMAIL", "contacto@erpparaguay.com")
    WEBSITE: str = os.getenv("COMPANY_WEBSITE", "www.erpparaguay.com")
    TAX_ID: str = os.getenv("COMPANY_TAX_ID", "12345678-9")

    @classmethod
    def to_dict(cls) -> Dict[str, str]:
        """Convert company settings to dictionary.

        Returns:
            Dictionary with all company settings
        """
        return {
            'name': cls.NAME,
            'address': cls.ADDRESS,
            'phone': cls.PHONE,
            'email': cls.EMAIL,
            'website': cls.WEBSITE,
            'tax_id': cls.TAX_ID
        }

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate company settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if not cls.NAME or cls.NAME == "ERP Paraguay":
            return False, "COMPANY_NAME not configured. Please set in .env file"

        if not cls.TAX_ID or cls.TAX_ID == "12345678-9":
            return False, "COMPANY_TAX_ID not configured. Please set your actual tax ID in .env file"

        return True, None


class TaxSettings:
    """Tax and financial calculation settings."""

    # Tax rate (as decimal, e.g., 0.10 for 10%)
    RATE: float = float(os.getenv("TAX_RATE", "0.10"))

    # Tax name for display (e.g., "IVA", "VAT", "Sales Tax")
    NAME: str = os.getenv("TAX_NAME", "IVA")

    # Tax display format (e.g., "IVA (10%)", "10% IVA")
    DISPLAY_FORMAT: str = os.getenv("TAX_DISPLAY_FORMAT", "{name} ({rate}%)")

    @classmethod
    def get_display_string(cls) -> str:
        """Get formatted tax display string.

        Returns:
            Formatted tax string (e.g., "IVA (10%)")
        """
        rate_percent = cls.RATE * 100
        return cls.DISPLAY_FORMAT.format(name=cls.NAME, rate=rate_percent)

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate tax settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.RATE < 0 or cls.RATE > 1:
            return False, f"TAX_RATE must be between 0 and 1, got {cls.RATE}"

        return True, None


class InvoiceSettings:
    """Invoice and PDF generation settings."""

    # Invoice settings
    PREFIX: str = os.getenv("INVOICE_PREFIX", "FAC")
    START_NUMBER: int = int(os.getenv("INVOICE_START_NUMBER", "1"))
    PADDING: int = int(os.getenv("INVOICE_NUMBER_PADDING", "6"))

    # Invoice terms (default payment terms in days)
    DEFAULT_PAYMENT_TERMS: int = int(os.getenv("INVOICE_PAYMENT_TERMS", "30"))

    # Invoice notes
    DEFAULT_NOTES: str = os.getenv(
        "INVOICE_DEFAULT_NOTES",
        "Gracias por su compra. Para cualquier consulta, contáctenos."
    )

    # Currency formatting
    CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "ₓ")
    CURRENCY_CODE: str = os.getenv("CURRENCY_CODE", "PYG")
    DECIMAL_PLACES: int = int(os.getenv("CURRENCY_DECIMALS", "2"))
    THOUSANDS_SEPARATOR: str = os.getenv("THOUSANDS_SEPARATOR", ",")

    @classmethod
    def format_invoice_number(cls, number: int) -> str:
        """Format an invoice number with prefix and padding.

        Args:
            number: The invoice number

        Returns:
            Formatted invoice number (e.g., "FAC-000001")
        """
        return f"{cls.PREFIX}-{str(number).zfill(cls.PADDING)}"

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate invoice settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.START_NUMBER < 1:
            return False, f"INVOICE_START_NUMBER must be positive, got {cls.START_NUMBER}"

        if cls.PADDING < 1 or cls.PADDING > 10:
            return False, f"INVOICE_NUMBER_PADDING must be between 1 and 10, got {cls.PADDING}"

        if cls.DEFAULT_PAYMENT_TERMS < 0:
            return False, f"INVOICE_PAYMENT_TERMS cannot be negative, got {cls.DEFAULT_PAYMENT_TERMS}"

        return True, None


class InventorySettings:
    """Inventory and stock management settings."""

    # Default reorder point for products
    DEFAULT_REORDER_POINT: float = float(os.getenv("DEFAULT_REORDER_POINT", "10"))

    # Low stock alert threshold
    LOW_STOCK_THRESHOLD: float = float(os.getenv("LOW_STOCK_THRESHOLD", "10"))

    # Allow negative stock (for backorders)
    ALLOW_NEGATIVE_STOCK: bool = os.getenv("ALLOW_NEGATIVE_STOCK", "false").lower() == "true"

    # Stock movement tracking
    TRACK_MOVEMENTS: bool = os.getenv("TRACK_STOCK_MOVEMENTS", "true").lower() == "true"

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate inventory settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.DEFAULT_REORDER_POINT < 0:
            return False, f"DEFAULT_REORDER_POINT cannot be negative, got {cls.DEFAULT_REORDER_POINT}"

        if cls.LOW_STOCK_THRESHOLD < 0:
            return False, f"LOW_STOCK_THRESHOLD cannot be negative, got {cls.LOW_STOCK_THRESHOLD}"

        return True, None


class ReportSettings:
    """Report generation settings."""

    # Default date range for reports (in days)
    DEFAULT_DATE_RANGE: int = int(os.getenv("REPORT_DEFAULT_DATE_RANGE", "30"))

    # Maximum rows in report before requiring pagination
    MAX_REPORT_ROWS: int = int(os.getenv("REPORT_MAX_ROWS", "1000"))

    # Report output format (pdf, html, excel)
    DEFAULT_FORMAT: str = os.getenv("REPORT_DEFAULT_FORMAT", "pdf")

    # Include company logo in reports (path to logo file)
    LOGO_PATH: Optional[str] = os.getenv("REPORT_LOGO_PATH")

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate report settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.DEFAULT_DATE_RANGE < 1:
            return False, f"REPORT_DEFAULT_DATE_RANGE must be positive, got {cls.DEFAULT_DATE_RANGE}"

        if cls.MAX_REPORT_ROWS < 1:
            return False, f"REPORT_MAX_ROWS must be positive, got {cls.MAX_REPORT_ROWS}"

        if cls.DEFAULT_FORMAT not in ['pdf', 'html', 'excel', 'csv']:
            return False, f"REPORT_DEFAULT_FORMAT must be one of: pdf, html, excel, csv, got {cls.DEFAULT_FORMAT}"

        return True, None


class SecuritySettings:
    """Security and authentication settings."""

    # Password requirements
    MIN_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
    REQUIRE_UPPERCASE: bool = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
    REQUIRE_LOWERCASE: bool = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
    REQUIRE_DIGIT: bool = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
    REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "false").lower() == "true"

    # Session settings
    TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    REMEMBER_ME_DAYS: int = int(os.getenv("SESSION_REMEMBER_ME_DAYS", "30"))

    # Login rate limiting
    MAX_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    BLOCK_MINUTES: int = int(os.getenv("LOGIN_BLOCK_MINUTES", "15"))

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate security settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.MIN_LENGTH < 8:
            return False, f"MIN_PASSWORD_LENGTH must be at least 8 for security, got {cls.MIN_LENGTH}"

        if cls.TIMEOUT_MINUTES < 5:
            return False, f"SESSION_TIMEOUT_MINUTES must be at least 5 minutes, got {cls.TIMEOUT_MINUTES}"

        if cls.MAX_ATTEMPTS < 3:
            return False, f"MAX_LOGIN_ATTEMPTS should be at least 3 for security, got {cls.MAX_ATTEMPTS}"

        return True, None


class UISettings:
    """User interface and display settings."""

    # Date format for display
    DATE_FORMAT: str = os.getenv("UI_DATE_FORMAT", "%d/%m/%Y")
    DATETIME_FORMAT: str = os.getenv("UI_DATETIME_FORMAT", "%d/%m/%Y %H:%M")

    # Number formatting
    DECIMAL_SEPARATOR: str = os.getenv("UI_DECIMAL_SEPARATOR", ",")
    THOUSANDS_SEPARATOR: str = os.getenv("UI_THOUSANDS_SEPARATOR", ".")

    # Table settings
    DEFAULT_PAGE_SIZE: int = int(os.getenv("UI_DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE: int = int(os.getenv("UI_MAX_PAGE_SIZE", "500"))

    # Theme colors (hex)
    PRIMARY_COLOR: str = os.getenv("UI_PRIMARY_COLOR", "#1a5276")
    SECONDARY_COLOR: str = os.getenv("UI_SECONDARY_COLOR", "#5499c7")
    SUCCESS_COLOR: str = os.getenv("UI_SUCCESS_COLOR", "#27ae60")
    WARNING_COLOR: str = os.getenv("UI_WARNING_COLOR", "#f39c12")
    DANGER_COLOR: str = os.getenv("UI_DANGER_COLOR", "#e74c3c")

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """Validate UI settings.

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if cls.DEFAULT_PAGE_SIZE < 1:
            return False, f"UI_DEFAULT_PAGE_SIZE must be positive, got {cls.DEFAULT_PAGE_SIZE}"

        if cls.MAX_PAGE_SIZE < cls.DEFAULT_PAGE_SIZE:
            return False, "UI_MAX_PAGE_SIZE must be greater than or equal to UI_DEFAULT_PAGE_SIZE"

        return True, None


def validate_all_settings() -> Dict[str, Any]:
    """Validate all application settings.

    Returns:
        Dictionary with validation results:
            - valid: Overall validity
            - errors: List of error messages
            - warnings: List of warnings
    """
    errors = []
    warnings = []

    # Validate each settings group
    settings_classes = [
        CompanySettings,
        TaxSettings,
        InvoiceSettings,
        InventorySettings,
        ReportSettings,
        SecuritySettings,
        UISettings
    ]

    all_valid = True
    for settings_class in settings_classes:
        valid, error = settings_class.validate()
        if not valid:
            all_valid = False
            errors.append(f"{settings_class.__name__}: {error}")

    # Check for default values that should be changed
    if CompanySettings.NAME == "ERP Paraguay":
        warnings.append("Company name is set to default 'ERP Paraguay'. Please update COMPANY_NAME.")

    if CompanySettings.TAX_ID == "12345678-9":
        warnings.append("Company tax ID is set to default value. Please update COMPANY_TAX_ID.")

    return {
        'valid': all_valid,
        'errors': errors,
        'warnings': warnings
    }


def get_settings_summary() -> Dict[str, Dict[str, Any]]:
    """Get a summary of all settings (excluding sensitive data).

    Returns:
        Dictionary with settings summary grouped by category
    """
    return {
        'company': {
            'name': CompanySettings.NAME,
            'tax_id': CompanySettings.TAX_ID[:3] + '***' if CompanySettings.TAX_ID else None,  # Partially mask
            'email': CompanySettings.EMAIL,
            'phone': CompanySettings.PHONE
        },
        'tax': {
            'rate': TaxSettings.RATE,
            'name': TaxSettings.NAME,
            'display': TaxSettings.get_display_string()
        },
        'invoice': {
            'prefix': InvoiceSettings.PREFIX,
            'start_number': InvoiceSettings.START_NUMBER,
            'currency_code': InvoiceSettings.CURRENCY_CODE
        },
        'inventory': {
            'default_reorder_point': InventorySettings.DEFAULT_REORDER_POINT,
            'low_stock_threshold': InventorySettings.LOW_STOCK_THRESHOLD,
            'allow_negative_stock': InventorySettings.ALLOW_NEGATIVE_STOCK
        },
        'security': {
            'session_timeout_minutes': SecuritySettings.TIMEOUT_MINUTES,
            'max_login_attempts': SecuritySettings.MAX_ATTEMPTS,
            'min_password_length': SecuritySettings.MIN_LENGTH
        },
        'ui': {
            'date_format': UISettings.DATE_FORMAT,
            'default_page_size': UISettings.DEFAULT_PAGE_SIZE,
            'primary_color': UISettings.PRIMARY_COLOR
        }
    }
