# ERP Paraguay V6 - System Architecture

This document provides an overview of the ERP Paraguay V6 system architecture, including the layered design, component interactions, and data flow.

## Architecture Overview

ERP Paraguay V6 follows a **three-tier layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│                        (UI Layer)                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Login UI  │  │  Dashboard │  │  Forms UI  │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│                      (Services Layer)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Service │  │ Sales Svc    │  │ Product Svc  │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ Customer Svc │  │ Inventory Svc│  │ Report Svc   │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ Financial Svc│  │ User Svc     │  │ Category Svc │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                       │
│                   (Repository & Database)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Base Repo     │  │ Transaction  │  │   Cache      │      │
│  │(Generic CRUD)│  │  Manager     │  │  (In-Memory) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│                  (11 Tables + Relationships)                 │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (UI)
- **Technology**: Tkinter (Python GUI)
- **Location**: `app/ui/`
- **Responsibilities**:
  - Display forms and windows
  - Handle user input
  - Validate basic input format
  - Display error messages
  - Manage session state
- **Key Components**:
  - `main_window.py` - Main application window and login
  - `sales_window.py` - Sales management UI
  - `customers_window.py` - Customer management UI
  - `suppliers_window.py` - Supplier management UI
  - Other specialized UI components

### Business Logic Layer (Services)
- **Location**: `app/services/`
- **Responsibilities**:
  - Implement business rules
  - Validate business constraints
  - Coordinate data operations
  - Handle errors and exceptions
  - Manage transactions
  - Apply business logic
- **Key Components**:
  - `auth_service.py` - Authentication and authorization
  - `sales_management_service.py` - Sales workflow
  - `customer_service.py` - Customer management
  - `product_service.py` - Product catalog
  - `financial_service.py` - Financial operations
  - `reports_service.py` - Report generation
  - Other service modules

### Data Access Layer
- **Location**: `app/database/`
- **Responsibilities**:
  - Database connection management
  - ORM model definitions
  - CRUD operations
  - Transaction management
  - Query optimization
  - Caching
- **Key Components**:
  - `db.py` - Database engine and session management
  - `models.py` - SQLAlchemy ORM models
  - `repository.py` - Generic repository pattern
  - `init_db.py` - Database initialization

## Component Interactions

### User Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Login Window
    participant Auth as Auth Service
    participant DB as Database
    participant Cache as Cache

    User->>UI: Enter credentials
    UI->>Auth: authenticate_user(username, password)
    Auth->>Auth: Check rate limit
    Auth->>DB: Query user by username
    DB-->>Auth: User record
    Auth->>Auth: Verify password hash
    Auth->>DB: Log authentication attempt
    Auth-->>UI: (success, error, user_data)
    UI->>User: Show result

    alt Success
        UI->>UI: Start session timer
        UI->>Cache: Cache user session
        UI->>UI: Show main dashboard
    else Failed
        Auth->>Auth: Increment failed attempts
        alt Max attempts reached
            Auth->>Auth: Lock account (15 min)
        end
        UI->>User: Show error message
    end
```

### Sales Creation Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Sales Window
    participant SalesSvc as Sales Service
    participant ProdSvc as Product Service
    participant CustSvc as Customer Service
    participant Txn as Transaction Manager
    participant DB as Database
    participant Cache as Cache

    User->>UI: Create sale with items
    UI->>SalesSvc: create_sale(customer_id, items, payment)
    SalesSvc->>CustSvc: get_customer_by_id(customer_id)
    CustSvc->>Cache: Check cache
    alt Cache hit
        Cache-->>CustSvc: Customer data
    else Cache miss
        CustSvc->>DB: Query customer
        DB-->>CustSvc: Customer record
        CustSvc->>Cache: Cache customer
    end
    CustSvc-->>SalesSvc: Customer object

    loop For each sale item
        SalesSvc->>ProdSvc: get_product_by_id(product_id)
        ProdSvc->>DB: Query product
        DB-->>ProdSvc: Product record
        ProdSvc-->>SalesSvc: Product object
        SalesSvc->>SalesSvc: Validate stock availability
        SalesSvc->>SalesSvc: Calculate line total
    end

    SalesSvc->>Txn: Begin transaction
    SalesSvc->>DB: Create sale record
    SalesSvc->>DB: Create sale items
    SalesSvc->>DB: Update product stock
    SalesSvc->>DB: Create payment (if not credit)
    SalesSvc->>Cache: Invalidate product cache
    SalesSvc->>Txn: Commit transaction
    Txn-->>SalesSvc: Transaction committed
    SalesSvc-->>UI: (success, error, sale_id)
    UI->>User: Display confirmation
```

### Report Generation Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Reports Window
    participant ReportSvc as Reports Service
    participant DB as Database
    participant PDF as PDF Generator
    participant Cache as Cache

    User->>UI: Request sales report
    UI->>ReportSvc: get_sales_summary(start_date, end_date)
    ReportSvc->>Cache: Check cache

    alt Cache hit
        Cache-->>ReportSvc: Cached report data
    else Cache miss
        ReportSvc->>DB: Query sales with eager loading
        Note over ReportSvc,DB: joinedload(), selectinload()<br/>Prevent N+1 queries
        DB-->>ReportSvc: Sales with items and products
        ReportSvc->>ReportSvc: Calculate summaries
        ReportSvc->>Cache: Cache result
    end

    ReportSvc-->>UI: Report data
    UI->>PDF: Generate PDF report
    PDF->>PDF: Apply company settings
    PDF->>PDF: Format with tax info
    PDF-->>UI: PDF document
    UI->>User: Display/save PDF
```

## Data Flow Patterns

### CRUD Operations Pattern

All data access follows the **Repository Pattern**:

```
UI → Service → Repository → Database → Cache
```

1. **UI Layer**: Receives user request
2. **Service Layer**: Applies business logic
3. **Repository Layer**: Executes database operations
4. **Cache Layer**: Caches frequently-accessed data
5. **Database**: Persists data

### Error Handling Pattern

All layers follow the **Result[T] pattern** for consistent error handling:

```python
# Service layer returns:
Result[T] = Tuple[bool, Optional[str], Optional[T]]

# Where:
# - bool: Success (True) or Failure (False)
# - Optional[str]: Error message (None if success)
# - Optional[T]: Result data (None if failure)
```

### Transaction Management Pattern

Complex operations use **Nested Transactions** with savepoints:

```mermaid
graph TD
    A[Begin Transaction] --> B{Operation 1}
    B -->|Success| C[Begin Savepoint 1]
    B -->|Failure| Z[Rollback Transaction]
    C --> D{Operation 2}
    D -->|Success| E[Begin Savepoint 2]
    D -->|Failure| Y[Rollback to Savepoint 1]
    E --> F{Operation 3}
    F -->|Success| G[Commit Transaction]
    F -->|Failure| X[Rollback to Savepoint 2]
    Y --> G
    X --> Y
```

## Security Architecture

### Authentication & Authorization

```mermaid
graph TB
    A[User] --> B{Authenticate}
    B -->|Valid| C[Create Session]
    B -->|Invalid| D[Log Failed Attempt]
    D --> E{Attempts >= 5?}
    E -->|Yes| F[Lock Account 15 min]
    E -->|No| G[Show Error]
    C --> H[Session Timer]
    H --> I{Inactivity > 60min?}
    I -->|Yes| J[Auto-Logout]
    I -->|No| K[Continue Session]
    F --> L[Wait 15 min]
    L --> B
```

### Audit Logging

All security events are logged with structured JSON format:

```json
{
  "timestamp": "2025-03-14T10:30:45Z",
  "level": "INFO",
  "logger": "app.services.auth_service",
  "message": "User login successful",
  "environment": "production",
  "user_id": 1,
  "username": "admin",
  "ip_address": "192.168.1.100",
  "request_id": "abc123"
}
```

## Performance Architecture

### Caching Strategy

```mermaid
graph LR
    A[Request] --> B{Check Cache}
    B -->|Hit| C[Return Cached Data]
    B -->|Miss| D[Query Database]
    D --> E[Cache Result with TTL]
    E --> C
    C --> F[Return to Service]
```

**Cache TTL Configuration:**
- Categories: 1 hour (3600s)
- Products: 5 minutes (300s)
- Customers: 10 minutes (600s)
- Suppliers: 10 minutes (600s)
- Settings: 30 minutes (1800s)

### Query Optimization

The application uses **SQLAlchemy eager loading** to prevent N+1 queries:

```python
# Before (N+1 problem):
sales = db.query(Sale).all()
for sale in sales:
    print(sale.items)  # N+1 query!

# After (optimized):
sales = db.query(Sale).options(
    selectinload(Sale.items)
).all()
for sale in sales:
    print(sale.items)  # No additional query
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Tkinter | Desktop GUI framework |
| **Business Logic** | Python 3.11+ | Service layer implementation |
| **Data Access** | SQLAlchemy 2.0+ | ORM and database abstraction |
| **Database** | PostgreSQL 14+ | Relational data storage |
| **Caching** | functools.lru_cache | In-memory caching |
| **PDF Generation** | ReportLab | Report generation |
| **Password Hashing** | passlib + bcrypt | Secure password storage |
| **Logging** | Python logging + JSON | Structured logging |
| **Testing** | pytest | Unit and integration tests |

## File Structure

```
erpnexos/
├── main.py                          # Application entry point
├── app/
│   ├── config.py                    # Configuration management
│   ├── settings.py                  # Business settings groups
│   ├── types.py                     # Type aliases
│   ├── exceptions.py                # Custom exceptions
│   ├── cache.py                     # Caching layer
│   ├── validators.py                # Input validators
│   ├── database/
│   │   ├── db.py                    # Database engine
│   │   ├── models.py                # ORM models
│   │   ├── repository.py            # Base repository
│   │   └── init_db.py               # Database initialization
│   ├── services/
│   │   ├── auth_service.py          # Authentication
│   │   ├── sales_management_service.py  # Sales workflow
│   │   ├── customer_service.py      # Customer management
│   │   ├── product_service.py       # Product catalog
│   │   ├── financial_service.py     # Financial operations
│   │   ├── reports_service.py       # Report generation
│   │   └── ...                      # Other services
│   ├── ui/
│   │   ├── main_window.py           # Main window
│   │   ├── sales_window.py          # Sales UI
│   │   ├── customers_window.py      # Customer UI
│   │   └── ...                      # Other UI modules
│   └── reports/
│       ├── pdf_reports.py           # PDF generation
│       └── pdf_helpers.py           # PDF utilities
├── tests/
│   ├── conftest.py                  # Test fixtures
│   ├── test_services/               # Service tests
│   ├── test_integration/            # Integration tests
│   └── test_*.py                    # Other test files
├── docs/
│   └── diagrams/                    # Architecture diagrams
├── logs/                            # Application logs
├── .env.example                     # Environment template
└── requirements.txt                 # Dependencies
```

## Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Repository Pattern** | `app/database/repository.py` | Generic CRUD operations |
| **Service Layer Pattern** | `app/services/` | Business logic encapsulation |
| **Singleton Pattern** | `app/cache.py` | Single cache instance |
| **Factory Pattern** | `app/database/db.py` | Session creation |
| **Result Pattern** | `app/types.py` | Consistent error handling |
| **Decorator Pattern** | `app/cache.py` | Caching decorator |
| **Template Method** | `app/database/repository.py` | Base repository template |
| **Strategy Pattern** | `app/reports/pdf_reports.py` | Report generation strategies |

## Scalability Considerations

### Current Architecture (Desktop)
- Single-user desktop application
- In-memory caching
- Direct database connections
- Suitable for small businesses

### Future Scalability Options

1. **Multi-User Support**
   - Add user roles and permissions
   - Implement row-level security
   - Add concurrent access control

2. **Client-Server Architecture**
   - Separate UI to client application
   - Expose services via REST API
   - Add authentication middleware

3. **Database Optimization**
   - Add read replicas for reporting
   - Implement connection pooling
   - Add database indexing strategy

4. **Distributed Caching**
   - Replace in-memory cache with Redis
   - Implement cache invalidation strategy
   - Add cache warming on startup

---

**Document Version:** 1.0
**Last Updated:** 2025-03-14
