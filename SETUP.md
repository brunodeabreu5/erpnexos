# ERP Paraguay V6 - Setup Guide

This guide will help you install, configure, and run ERP Paraguay V6 on your system.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Building Windows Executable](#building-windows-executable)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [New Features](#new-features)

## Prerequisites

Before installing ERP Paraguay, ensure you have the following:

### Required Software

1. **Python 3.11 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **PostgreSQL 14 or higher**
   - Download from [postgresql.org](https://www.postgresql.org/download/windows/)
   - Note the password you set for the `postgres` user during installation

3. **Git** (optional, for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/downloads)

### Verify Installation

Open a terminal/command prompt and verify:

```bash
python --version
# Should show: Python 3.11.x or higher

psql --version
# Should show: psql (PostgreSQL) 14.x or higher
```

## Installation

### 1. Clone or Download the Repository

If using Git:
```bash
git clone https://github.com/your-username/erpnexos.git
cd erpnexos
```

Or download and extract the ZIP file.

### 2. Create a Virtual Environment (Recommended)

A virtual environment keeps your project dependencies isolated:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your command prompt when activated.

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This installs:
- **SQLAlchemy** (2.0+) - ORM for database operations
- **psycopg2-binary** - PostgreSQL adapter
- **python-dotenv** - Environment variables management
- **reportlab** - PDF generation for reports and invoices
- **passlib** - Password hashing with bcrypt
- **pyinstaller** - Windows executable building

## Configuration

### 1. Create Environment File

Copy the example environment file and modify it with your settings:

**Windows Command Prompt:**
```bash
copy .env.example .env
```

**Windows PowerShell:**
```bash
Copy-Item .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

### 2. Configure Required Variables

Open `.env` in a text editor. **The following variables are REQUIRED and must be configured:**

#### Database Configuration (REQUIRED)
```env
# IMPORTANT: Replace 'your_secure_password' with your PostgreSQL password
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/erp_paraguay
```

#### Administrator Account (REQUIRED)
```env
# Administrator credentials - REQUIRED for first-time setup
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password_here
```

**IMPORTANT SECURITY NOTES:**
- The application will **NOT start** without `ADMIN_PASSWORD` configured
- The old default password `admin/admin123` has been removed for security
- Use a strong password (minimum 8 characters, recommended 12+)
- Never use common passwords like "password123" or "admin123"

#### Environment Configuration (REQUIRED)
```env
# Environment: development, staging, or production
ENVIRONMENT=development

# Debug mode (set to false in production)
DEBUG=false

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

### 3. Configure Optional Variables

The following variables have defaults but should be customized for your needs:

#### Company Information (Recommended for Production)
```env
# Company details for invoices and reports
COMPANY_NAME=My Company Name
COMPANY_ADDRESS=Your Business Address
COMPANY_PHONE=+595 21 123 456
COMPANY_EMAIL=contacto@yourcompany.com
COMPANY_TAX_ID=12345678-9
```

#### Tax Configuration
```env
# Tax rate and display settings
TAX_RATE=0.10
TAX_NAME=IVA
TAX_DISPLAY_FORMAT={name} ({rate}%)
```

#### Invoice Settings
```env
# Invoice numbering and format
INVOICE_PREFIX=FAC
INVOICE_START_NUMBER=1
INVOICE_NUMBER_PADDING=6
CURRENCY_SYMBOL=ₓ
CURRENCY_CODE=PYG
```

#### Security Settings
```env
# Password and session security
MIN_PASSWORD_LENGTH=8
SESSION_TIMEOUT_MINUTES=60
MAX_LOGIN_ATTEMPTS=5
LOGIN_BLOCK_MINUTES=15
```

#### Inventory Settings
```env
# Stock management
LOW_STOCK_THRESHOLD=10
DEFAULT_STOCK=0
```

#### Cache Settings
```env
# Performance caching (in seconds)
CACHE_ENABLED=true
CATEGORIES_CACHE_TTL=3600
PRODUCTS_CACHE_TTL=300
CUSTOMERS_CACHE_TTL=600
SUPPLIERS_CACHE_TTL=600
SETTINGS_CACHE_TTL=1800
```

#### UI Settings
```env
# User interface configuration
UI_THEME=default
WINDOW_WIDTH=1200
WINDOW_HEIGHT=700
```

**Security Note:**
- Never commit `.env` to version control (it's in `.gitignore`)
- Use strong, unique passwords in production
- Keep `.env` file permissions restricted (user-readable only)

## Database Setup

### 1. Create the Database

Using PostgreSQL's `psql` command-line tool:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE erp_paraguay;

# Exit psql
\q
```

Or use pgAdmin (GUI) to create a database named `erp_paraguay`.

### 2. Initialize Database Schema

Run the database initialization script:

```bash
python -m app.database.init_db
```

This will:
- Create all required tables (users, products, customers, sales, etc.)
- Create relationships and constraints
- Create the admin user using credentials from `.env`
- Validate configuration settings

**Expected Output:**
```
Initializing database...
Creating tables...
Creating admin user...
Database initialized successfully!

Admin credentials:
  Username: admin
  Password: [from ADMIN_PASSWORD in .env]

IMPORTANT: Keep your admin password secure!
```

### 3. Verify Database Initialization

Check that tables were created:

```bash
psql -U postgres -d erp_paraguay -c "\dt"
```

You should see tables:
- `users` - System users
- `products` - Product catalog
- `categories` - Product categories
- `customers` - Customer records
- `suppliers` - Supplier information
- `sales` - Sales transactions
- `sale_items` - Line items for sales
- `payments` - Payment records
- `expenses` - Business expenses
- `audit_logs` - Security audit trail

### 4. Configuration Validation

At startup, the application validates all configuration:

- **Production Environment**: Requires MIN_PASSWORD_LENGTH ≥ 8, DEBUG=false
- **Required Variables**: DATABASE_URL, ADMIN_PASSWORD, ENVIRONMENT
- **Company Settings**: Validates in production if COMPANY_NAME is set to default

If validation fails, the application will display detailed errors and exit.

## Running the Application

### Development Mode

Simply run the main application:

```bash
python main.py
```

The login window will appear. Use the credentials you configured in `.env`:
- Username: `[value of ADMIN_USERNAME]`
- Password: `[value of ADMIN_PASSWORD]`

**First Steps:**
1. Login with your configured admin credentials
2. Verify dashboard loads correctly
3. Configure company settings if not set in `.env`
4. Create product categories
5. Add products to inventory
6. Start managing sales and customers

### Session Management

The application includes automatic session management:
- Sessions expire after `SESSION_TIMEOUT_MINUTES` (default: 60 minutes)
- Inactivity timer resets on user actions
- Automatic logout with notification when session expires
- Session checker runs every 60 seconds

### Login Security

The application includes enhanced security features:
- **Rate Limiting**: 5 failed login attempts trigger a 15-minute block
- **Audit Logging**: All login attempts are logged with timestamps
- **Password Validation**: Enforces minimum length requirements
- **Session Timeout**: Automatic logout after inactivity

### Logs

Application logs are stored in the `logs/` directory with structured JSON format:
- `app.log` - Current log file (JSON format)
- `app.log.1`, `app.log.2`, etc. - Rotated backup logs

**Log Format:**
```json
{
  "timestamp": "2025-03-14T10:30:45Z",
  "level": "INFO",
  "logger": "app.services.auth_service",
  "message": "User login successful",
  "environment": "production",
  "user_id": 1,
  "request_id": "abc123"
}
```

View logs in real-time:
```bash
# Windows (PowerShell)
Get-Content logs\app.log -Wait -Tail 20

# Linux/Mac
tail -f logs/app.log
```

### Caching

The application includes intelligent caching to improve performance:
- Categories cached for 1 hour
- Products cached for 5 minutes
- Customers and suppliers cached for 10 minutes
- Settings cached for 30 minutes

Cache is automatically invalidated when data changes.

## Building Windows Executable

To create a standalone `.exe` file that doesn't require Python installation:

### Using the Build Script

**Windows:**
```bash
build_windows.bat
```

This will:
1. Install all dependencies
2. Build the executable using PyInstaller
3. Create a `dist/` folder with `ERP_Paraguay.exe`

### Manual Build

If you prefer more control over the build process:

```bash
pyinstaller --onefile --windowed --name ERP_Paraguay main.py
```

The executable will be in `dist/ERP_Paraguay.exe`.

**Note:** The first time you run the executable, it may take longer to start as PyInstaller extracts files.

## Troubleshooting

### Common Issues

#### 1. "ADMIN_PASSWORD environment variable not set" Error

**Problem:** Application won't start because admin password is not configured

**Solutions:**
- Open `.env` file and add: `ADMIN_PASSWORD=your_secure_password`
- Ensure `.env` exists (copy from `.env.example`)
- Don't use `.env.example` directly
- Minimum password length: 8 characters

#### 2. "Account is temporarily locked" Error

**Problem:** Account locked due to too many failed login attempts

**Solutions:**
- Wait 15 minutes for the lock to expire
- Or restart the application to clear in-memory lock counter
- Check logs for suspicious activity
- Verify you're using the correct password

#### 3. "connection to server at socket" Error

**Problem:** Cannot connect to PostgreSQL

**Solutions:**
- Verify PostgreSQL is running: Check Services for "postgresql-x64-14"
- Verify password in `DATABASE_URL` matches your PostgreSQL password
- Check that the database exists: `psql -U postgres -l | grep erp_paraguay`
- Ensure PostgreSQL is accepting connections on port 5432

#### 4. "Session expired" Notification

**Problem:** Application logged out due to inactivity

**Solutions:**
- This is normal security behavior after 60 minutes of inactivity
- Adjust `SESSION_TIMEOUT_MINUTES` in `.env` if needed
- Save your work before stepping away

#### 5. "No module named 'app'" Error

**Problem:** Python can't find the app module

**Solutions:**
- Ensure you're in the project root directory (where `main.py` is)
- Install in editable mode: `pip install -e .`
- Check your PYTHONPATH includes the project directory
- Verify virtual environment is activated

#### 6. Configuration Validation Failed

**Problem:** Application exits with validation errors

**Solutions:**
- Check the error message for specific validation failures
- Production requires: MIN_PASSWORD_LENGTH ≥ 8, DEBUG=false
- Ensure COMPANY_NAME is customized in production
- All required variables must be set in `.env`

#### 7. Permission Denied Errors

**Problem:** Cannot write to logs directory

**Solutions:**
- Run as administrator (Windows) or with appropriate permissions
- Manually create the `logs/` directory
- Check `LOG_DIR` in `.env` points to a writable location

#### 8. Performance Issues

**Problem:** Application is slow or unresponsive

**Solutions:**
- Check cache is enabled: `CACHE_ENABLED=true`
- Review logs for database query performance
- Ensure database indexes are created
- Consider reducing cache TTL values for fresher data
- Check for N+1 query issues in logs

#### 9. PyInstaller Build Fails

**Problem:** Cannot create executable

**Solutions:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try building with `--debug` flag: `pyinstaller --debug --onefile main.py`
- Check PyInstaller log output for specific errors
- Verify no import errors in modules

#### 10. Import Errors on Startup

**Problem:** Module not found errors when running

**Solutions:**
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check Python version is 3.11+
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
- Verify virtual environment is activated

### Getting Help

If you encounter issues not covered here:

1. **Check Application Logs**
   - Logs are in structured JSON format
   - Look for error details with stack traces
   - Check for validation errors or missing configuration

2. **Enable Debug Mode**
   - Set `DEBUG=true` in `.env`
   - Restart the application
   - Review detailed error messages

3. **Review Configuration**
   - Verify all required variables in `.env`
   - Check for typos in variable names
   - Ensure no extra spaces around values

4. **Search Issues**
   - Check [GitHub Issues](https://github.com/your-username/erpnexos/issues)
   - Look for similar problems and solutions

5. **Submit a Bug Report**
   Include:
   - Error message and stack trace
   - Steps to reproduce the issue
   - Your OS and Python version
   - Relevant log excerpts (sanitize sensitive data)
   - Your `.env` configuration (with passwords removed)

## Security Best Practices

### For Development

1. **Strong Passwords**
   - Use a password manager to generate strong passwords
   - Minimum 8 characters, recommended 12+ characters
   - Mix of uppercase, lowercase, numbers, and symbols

2. **Environment Security**
   - Never commit `.env` to version control
   - Keep `.env` file permissions restricted
   - Use different credentials for development and production

3. **Keep Dependencies Updated**
   - Regularly run: `pip install --upgrade -r requirements.txt`
   - Check for security advisories in dependencies
   - Review dependency versions for vulnerabilities

4. **Secure Development Practices**
   - Don't hardcode credentials in code
   - Use environment variables for all configuration
   - Review code for security issues before committing

### For Production

1. **Environment Configuration**
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=false`
   - Use strong, unique passwords for all accounts
   - Use a dedicated database user (not `postgres`)

2. **Database Security**
   - Restrict database network access
   - Enable SSL for database connections
   - Regular database backups
   - Implement database user permissions

3. **Network Security**
   - Use HTTPS for web deployments
   - Implement firewall rules
   - Restrict access by IP if possible
   - Use VPN for remote access

4. **Monitoring and Logging**
   - Enable audit logging
   - Regularly review logs for suspicious activity
   - Set up alerts for security events
   - Monitor failed login attempts

5. **Backup Strategy**
   - Regular automated database backups
   - Backup configuration files (`.env`)
   - Document recovery procedures
   - Test backup restoration regularly

6. **Regular Security Audits**
   - Review user access rights
   - Rotate passwords periodically
   - Update dependencies
   - Review audit logs
   - Test security controls

## New Features

### Phase 1: Security Improvements

#### Enhanced Authentication
- **Removed hardcoded passwords**: Default admin credentials removed
- **Required configuration**: `ADMIN_PASSWORD` must be set in `.env`
- **Rate limiting**: 5 failed attempts trigger 15-minute lockout
- **Audit logging**: All login attempts logged with timestamps

#### Session Management
- **Automatic timeout**: Sessions expire after 60 minutes of inactivity
- **Activity tracking**: Last activity time tracked and logged
- **Auto-logout**: User notified and logged out on timeout
- **Session renewal**: Activity timer resets on user actions

### Phase 2: Code Refactoring

#### Repository Pattern
- **BaseRepository class**: Generic CRUD operations for all models
- **Type safety**: Generic type annotations for better IDE support
- **Code reduction**: ~60% reduction in duplicated CRUD code
- **Consistency**: Standardized data access patterns

#### Type System
- **Result[T] type alias**: Consistent error handling across services
- **Helper functions**: `success()` and `failure()` for creating results
- **Type hints**: Full type annotations for better code quality

### Phase 3: Error Handling

#### Custom Exceptions
- **Exception hierarchy**: Structured exception classes for all error types
- **Error codes**: Standardized error codes for easier debugging
- **Context information**: Exceptions include relevant details
- **User-friendly messages**: Clear error messages for end users

#### Transaction Management
- **Atomic transactions**: Complex operations use nested transactions
- **Automatic rollback**: Failures automatically rollback changes
- **Savepoint support**: Nested operations with independent rollback

#### Structured Logging
- **JSON format**: All logs in structured JSON for parsing
- **Request context**: Logs include request_id and user_id when available
- **Environment tagging**: All logs include environment name
- **Improved debugging**: Easier to trace issues through logs

### Phase 4: Performance

#### Query Optimization
- **Eager loading**: Fixed N+1 query problems in reports
- **joinedload()**: Optimize one-to-one relationship queries
- **selectinload()**: Optimize one-to-many relationship queries
- **~90% query reduction**: Significant performance improvement

#### Pagination
- **Paginated lists**: Large datasets loaded in pages
- **Metadata**: Total count, pages, and page size included
- **Configurable page size**: Adjustable via parameters
- **Memory efficiency**: Reduced memory usage for large datasets

#### Caching Layer
- **Simple cache**: Thread-safe in-memory cache with TTL
- **Cached decorator**: Easy function result caching
- **Multiple TTL types**: Different cache durations for data types
- **Automatic cleanup**: Expired entries removed automatically

### Phase 5: Configuration

#### Centralized Settings
- **Settings groups**: 7 configuration groups organized by domain
  - CompanySettings: Business information
  - TaxSettings: Tax calculation
  - InvoiceSettings: Invoice formatting
  - InventorySettings: Stock management
  - ReportSettings: Report generation
  - SecuritySettings: Authentication and sessions
  - UISettings: User interface
- **Externalized config**: All hardcoded values moved to `.env`
- **Validation**: Configuration validated at startup
- **Environment-specific**: Different rules for dev/staging/prod

#### Configuration Variables
- **50+ variables**: Comprehensive configuration options
- **Sensible defaults**: All variables have default values
- **Documentation**: Each variable documented in `.env.example`
- **Type conversion**: Automatic type conversion and validation

### Phase 6: Testing

#### Comprehensive Test Suite
- **147+ test cases**: Comprehensive coverage of functionality
- **7 test files**: Organized by module and feature
  - test_customer_service.py: Customer CRUD operations
  - test_supplier_service.py: Supplier CRUD operations
  - test_sales_management_service.py: Sales workflow
  - test_settings.py: Configuration validation
  - test_exceptions.py: Exception handling
  - test_integration/test_sales_flow.py: End-to-end workflows
- **80% coverage target**: High confidence in code correctness

#### Integration Tests
- **Complete workflows**: Tests for entire business processes
- **Multi-service**: Tests interactions between services
- **Critical paths**: Sales, payments, inventory, customer lifecycle

#### Test Fixtures
- **20+ fixtures**: Reusable test data and mocks
- **Organized**: Grouped by functionality
- **Easy to extend**: Simple patterns for new tests

## Next Steps

After successful setup:

1. **Read Documentation**
   - [CLAUDE.md](CLAUDE.md) - Development guidelines
   - [REVIEW_SUMMARY.md](REVIEW_SUMMARY.md) - Review and improvement plan

2. **Customize Configuration**
   - Set company information in `.env`
   - Configure tax rates for your region
   - Adjust security settings for your needs
   - Customize UI preferences

3. **Explore the Codebase**
   - `app/` - Main application code
   - `app/database/` - Data layer
   - `app/services/` - Business logic
   - `app/ui/` - User interface
   - `app/reports/` - Report generation

4. **Consider Enhancements**
   - Add more user roles and permissions
   - Implement multi-language support
   - Add barcode scanning for inventory
   - Integrate with payment gateways
   - Implement email notifications
   - Add dashboard analytics and charts

5. **Performance Tuning**
   - Adjust cache TTL values based on data volatility
   - Optimize page sizes for your typical datasets
   - Review database indexes for query patterns
   - Monitor query performance in logs

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [github.com/your-username/erpnexos/issues](https://github.com/your-username/erpnexos/issues)
- **Documentation**: [CLAUDE.md](CLAUDE.md)
- **Review Summary**: [REVIEW_SUMMARY.md](REVIEW_SUMMARY.md)

---

**Last Updated:** 2025-03-14
**Version:** 6.0.0
**Document Version:** 2.0
