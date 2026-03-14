# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ERP Paraguay V6 is a basic desktop ERP system in Python with Tkinter GUI and PostgreSQL database backend.

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python main.py
```

### Building Windows Executable
```bash
build_windows.bat
```
This installs dependencies and creates a standalone executable using PyInstaller.

### Database Initialization
The database schema is auto-created on first run via SQLAlchemy's `Base.metadata.create_all()`. Ensure PostgreSQL is running with the database configured in `app/config.py`.

## Architecture

The application follows a layered architecture with clear separation of concerns:

```
app/
├── config.py           # Database connection configuration
├── database/           # Data layer
│   ├── db.py          # SQLAlchemy engine, session, Base
│   ├── models.py      # ORM models (Product, etc.)
│   └── init_db.py     # Database initialization
├── services/          # Business logic layer
│   ├── auth_service.py
│   ├── dashboard_service.py
│   └── sales_service.py
├── reports/           # PDF generation
│   └── pdf_reports.py
└── ui/                # Presentation layer (Tkinter)
    └── main_window.py
```

### Key Patterns

- **Database Access**: Services use `SessionLocal()` to create database sessions. Sessions are not currently context-managed - new sessions are created per call.
- **UI Layer**: Tkinter-based desktop interface. The `App` class in `main_window.py` manages the root window and login flow.
- **Authentication**: Currently hardcoded in `auth_service.py` (admin/admin123).

### Database Configuration

Connection string is in `app/config.py`:
```python
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/erp_paraguay"
```

Default credentials for the GUI:
- Username: `admin`
- Password: `admin123`

## Dependencies

- **SQLAlchemy** - ORM for database operations
- **psycopg2-binary** - PostgreSQL adapter
- **Tkinter** - Desktop GUI (usually built-in with Python)
- **reportlab** - PDF report generation
- **passlib** - Password hashing (not yet utilized)
- **pyinstaller** - Windows executable packaging
