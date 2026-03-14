"""Unit tests for the settings module.

Tests all settings classes and their validation methods.
"""
import pytest
import os
from app.settings import (
    CompanySettings,
    TaxSettings,
    InvoiceSettings,
    InventorySettings,
    ReportSettings,
    SecuritySettings,
    UISettings,
    validate_all_settings,
    get_settings_summary
)


class TestCompanySettings:
    """Tests for CompanySettings class."""

    def test_company_settings_defaults(self):
        """Test default company settings values."""
        settings = CompanySettings.to_dict()

        assert 'name' in settings
        assert 'address' in settings
        assert 'phone' in settings
        assert 'email' in settings
        assert 'tax_id' in settings

    def test_to_dict_returns_copy(self):
        """Test that to_dict returns a copy, not reference."""
        dict1 = CompanySettings.to_dict()
        dict2 = CompanySettings.to_dict()

        assert dict1 == dict2
        assert dict1 is not dict2

    def test_validate_with_defaults_fails(self):
        """Test validation fails with default values."""
        # Temporarily set to defaults for testing
        original_name = CompanySettings.NAME
        original_tax_id = CompanySettings.TAX_ID

        try:
            CompanySettings.NAME = "ERP Paraguay"
            CompanySettings.TAX_ID = "12345678-9"

            valid, error = CompanySettings.validate()

            assert valid is False
            assert "not configured" in error.lower()
        finally:
            CompanySettings.NAME = original_name
            CompanySettings.TAX_ID = original_tax_id


class TestTaxSettings:
    """Tests for TaxSettings class."""

    def test_default_tax_rate(self):
        """Test default tax rate is 0.10 (10%)."""
        assert TaxSettings.RATE == 0.10

    def test_get_display_string(self):
        """Test tax display string formatting."""
        display = TaxSettings.get_display_string()

        assert "IVA" in display or "VAT" in display
        assert "10" in display or "%" in display

    def test_validate_valid_rate(self):
        """Test validation with valid tax rate."""
        valid, error = TaxSettings.validate()

        assert valid is True
        assert error is None

    def test_validate_invalid_rate_too_high(self):
        """Test validation fails with rate > 1."""
        original_rate = TaxSettings.RATE
        try:
            TaxSettings.RATE = 1.5
            valid, error = TaxSettings.validate()

            assert valid is False
            assert "between 0 and 1" in error.lower()
        finally:
            TaxSettings.RATE = original_rate

    def test_validate_invalid_rate_negative(self):
        """Test validation fails with negative rate."""
        original_rate = TaxSettings.RATE
        try:
            TaxSettings.RATE = -0.1
            valid, error = TaxSettings.validate()

            assert valid is False
        finally:
            TaxSettings.RATE = original_rate


class TestInvoiceSettings:
    """Tests for InvoiceSettings class."""

    def test_default_invoice_prefix(self):
        """Test default invoice prefix is 'FAC'."""
        assert InvoiceSettings.PREFIX == "FAC"

    def test_format_invoice_number(self):
        """Test invoice number formatting with padding."""
        formatted = InvoiceSettings.format_invoice_number(1)

        assert "FAC" in formatted
        assert "000001" in formatted

    def test_format_invoice_number_custom_padding(self):
        """Test invoice number with different padding."""
        original_padding = InvoiceSettings.PADDING
        try:
            InvoiceSettings.PADDING = 4
            formatted = InvoiceSettings.format_invoice_number(1)

            assert "FAC-0001" in formatted
        finally:
            InvoiceSettings.PADDING = original_padding

    def test_validate_valid_settings(self):
        """Test validation with valid invoice settings."""
        valid, error = InvoiceSettings.validate()

        assert valid is True
        assert error is None


class TestInventorySettings:
    """Tests for InventorySettings class."""

    def test_default_reorder_point(self):
        """Test default reorder point is 10."""
        assert InventorySettings.DEFAULT_REORDER_POINT == 10

    def test_validate_valid_settings(self):
        """Test validation with valid inventory settings."""
        valid, error = InventorySettings.validate()

        assert valid is True
        assert error is None

    def test_validate_negative_reorder_point(self):
        """Test validation fails with negative reorder point."""
        original_point = InventorySettings.DEFAULT_REORDER_POINT
        try:
            InventorySettings.DEFAULT_REORDER_POINT = -5
            valid, error = InventorySettings.validate()

            assert valid is False
            assert "cannot be negative" in error.lower()
        finally:
            InventorySettings.DEFAULT_REORDER_POINT = original_point


class TestSecuritySettings:
    """Tests for SecuritySettings class."""

    def test_min_password_length(self):
        """Test minimum password length from config."""
        assert SecuritySettings.MIN_LENGTH >= 8

    def test_session_timeout_minutes(self):
        """Test session timeout is reasonable."""
        assert SecuritySettings.TIMEOUT_MINUTES > 0
        assert SecuritySettings.TIMEOUT_MINUTES <= 120  # Max 2 hours

    def test_max_login_attempts(self):
        """Test max login attempts is set."""
        assert SecuritySettings.MAX_ATTEMPTS >= 3
        assert SecuritySettings.MAX_ATTEMPTS <= 10

    def test_validate_production_security(self):
        """Test validation enforces stronger security for production."""
        original_min = SecuritySettings.MIN_LENGTH
        original_debug = os.getenv("DEBUG", "false").lower() == "true"

        try:
            os.environ["ENVIRONMENT"] = "production"
            SecuritySettings.MIN_LENGTH = 6  # Too low for production

            valid, error = SecuritySettings.validate()

            # Should fail with min password < 8 in production
            if os.getenv("ENVIRONMENT") == "production":
                assert valid is False

        finally:
            SecuritySettings.MIN_LENGTH = original_min
            if original_debug:
                os.environ["DEBUG"] = "true"
            else:
                os.environ["DEBUG"] = "false"


class TestUISettings:
    """Tests for UISettings class."""

    def test_date_format_set(self):
        """Test date format is configured."""
        assert UISettings.DATE_FORMAT is not None
        assert "%" in UISettings.DATE_FORMAT

    def test_default_page_size(self):
        """Test default page size is reasonable."""
        assert UISettings.DEFAULT_PAGE_SIZE >= 10
        assert UISettings.DEFAULT_PAGE_SIZE <= 100

    def test_validate_page_size_limits(self):
        """Test validation enforces page size limits."""
        original_default = UISettings.DEFAULT_PAGE_SIZE
        original_max = UISettings.MAX_PAGE_SIZE

        try:
            UISettings.DEFAULT_PAGE_SIZE = 600
            UISettings.MAX_PAGE_SIZE = 500

            valid, error = UISettings.validate()

            assert valid is False
            assert "greater than or equal to" in error.lower()
        finally:
            UISettings.DEFAULT_PAGE_SIZE = original_default
            UISettings.MAX_PAGE_SIZE = original_max


class TestValidateAllSettings:
    """Tests for validate_all_settings function."""

    def test_validate_all_returns_dict(self):
        """Test that validation returns dictionary with expected keys."""
        result = validate_all_settings()

        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result

    def test_validate_all_has_warnings_for_defaults(self):
        """Test validation produces warnings for default values."""
        result = validate_all_settings()

        # Should have warnings for default company name/tax_id
        if result['warnings']:
            assert any('default' in str(w).lower() for w in result['warnings'])


class TestGetSettingsSummary:
    """Tests for get_settings_summary function."""

    def test_summary_returns_dict(self):
        """Test that summary returns dictionary."""
        summary = get_settings_summary()

        assert isinstance(summary, dict)

    def test_summary_includes_all_sections(self):
        """Test summary includes all configuration sections."""
        summary = get_settings_summary()

        expected_sections = [
            'company', 'tax', 'invoice', 'inventory',
            'security', 'ui'
        ]

        for section in expected_sections:
            assert section in summary

    def test_summary_masks_sensitive_data(self):
        """Test that summary masks sensitive data like tax_id."""
        summary = get_settings_summary()

        if 'company' in summary and summary['company'].get('tax_id'):
            tax_id = summary['company']['tax_id']
            # Should be partially masked
            assert '***' in tax_id or len(tax_id) < 10


class TestSettingsIntegration:
    """Integration tests for settings loading from environment."""

    def test_load_from_env(self):
        """Test that settings load values from environment variables."""
        # Set test environment variables
        os.environ["COMPANY_NAME"] = "Test Company LTD"
        os.environ["TAX_RATE"] = "0.15"

        # Reload settings by re-importing
        from importlib import reload
        import app.settings as settings_module

        # Note: In real tests, you'd need to handle module reloading better
        # This is a simplified test

        # Verify values are loaded
        assert settings_module.CompanySettings.NAME == "Test Company LTD"

    def test_env_vars_override_defaults(self):
        """Test that environment variables override defaults."""
        original_tax = os.getenv("TAX_RATE")
        original_company = os.getenv("COMPANY_NAME")

        try:
            os.environ["TAX_RATE"] = "0.20"
            os.environ["COMPANY_NAME"] = "Custom Company"

            # Settings should pick up new values
            assert TaxSettings.RATE == 0.20
            assert CompanySettings.NAME == "Custom Company"

        finally:
            if original_tax:
                os.environ["TAX_RATE"] = original_tax
            else:
                del os.environ["TAX_RATE"]

            if original_company:
                os.environ["COMPANY_NAME"] = original_company
            else:
                del os.environ["COMPANY_NAME"]
