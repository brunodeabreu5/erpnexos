# ERP Paraguay V6 - Architecture Diagrams

This directory contains comprehensive architecture diagrams and workflow documentation for ERP Paraguay V6.

## Diagrams Overview

### 1. [architecture.md](architecture.md)
**System Architecture Documentation**

Complete overview of the ERP Paraguay V6 system architecture including:
- Three-tier layered architecture (UI → Services → Data)
- Component interactions and data flow
- Technology stack and design patterns
- Security architecture
- Performance optimization strategies
- Scalability considerations
- File structure and organization

**Key Diagrams:**
- User Authentication Flow
- Sales Creation Flow
- Report Generation Flow
- Data Flow Patterns
- Transaction Management Pattern
- Security Architecture
- Caching Strategy

**Best For:**
- Understanding overall system design
- Onboarding new developers
- Architecture review and planning
- Integration planning

---

### 2. [database_schema.md](database_schema.md)
**Database Schema Documentation**

Complete Entity-Relationship (ER) diagram and schema documentation including:
- ER diagram for all 12 tables
- Detailed table definitions with columns, types, and constraints
- Relationship mappings (one-to-many, many-to-one)
- Indexes and foreign key constraints
- Check constraints and business rules
- Database triggers
- Views for common queries
- Performance considerations

**Tables Documented:**
- users, customers, suppliers
- categories, products
- sales, sale_items, payments
- expenses, expense_categories
- stock_adjustments, audit_logs

**Best For:**
- Database design and optimization
- Writing complex queries
- Understanding data relationships
- Schema migrations and updates

---

### 3. [sales_workflow.md](sales_workflow.md)
**Sales Management Workflow**

Detailed flowcharts and documentation for the sales process including:
- Complete sales process flow (customer → items → payment)
- Cash sale detailed flow with sequence diagram
- Credit sale with payment flow
- Sale cancellation flow with stock restoration
- Multiple installments workflow
- Stock adjustment workflow
- Sales report generation flow
- Error handling in sales flow

**Key Workflows:**
- Creating a sale (cash, credit, debit, transfer)
- Processing payments and installments
- Cancelling sales and restoring stock
- Generating sales reports
- Managing stock levels

**Best For:**
- Understanding sales business logic
- Implementing sales features
- Troubleshooting sales issues
- Training users on sales process

---

### 4. [authentication_workflow.md](authentication_workflow.md)
**Authentication and Authorization Workflow**

Complete security flow documentation including:
- Login process flow (from app startup to dashboard)
- Rate limiting mechanism (5 attempts, 15-minute block)
- Session management (60-minute timeout)
- Password hashing and verification with bcrypt
- Audit logging flow
- Authorization flow (admin, seller, viewer roles)
- Security configuration validation
- Password recovery flow (future enhancement)

**Security Features:**
- Bcrypt password hashing (cost factor 12)
- Rate limiting for brute force protection
- Automatic session timeout
- Comprehensive audit logging
- Role-based access control

**Best For:**
- Understanding security architecture
- Implementing authentication features
- Security audits and reviews
- Troubleshooting login issues

---

### 5. [inventory_workflow.md](inventory_workflow.md)
**Inventory Management Workflow**

Complete inventory management flow documentation including:
- Product management overview
- Add new product flow
- Edit product flow
- Stock adjustment flow
- Low stock alert flow
- Product deletion flow (vs deactivation)
- Category management flow
- Supplier management flow
- Inventory report generation
- Batch import flow

**Inventory Features:**
- Product CRUD operations
- Stock tracking and adjustments
- Low stock alerts
- Category and supplier management
- Batch import/export
- Inventory valuation reports

**Best For:**
- Understanding inventory management
- Implementing inventory features
- Managing product data
- Generating inventory reports

---

## How to Use These Diagrams

### For New Developers

1. **Start with** `architecture.md` to understand the big picture
2. **Review** `database_schema.md` to understand the data model
3. **Study** the workflow documents relevant to your work area
4. **Reference** specific flows when implementing features

### For System Administrators

1. **Review** `authentication_workflow.md` for security setup
2. **Check** `database_schema.md` for database requirements
3. **Use** `inventory_workflow.md` for inventory management

### For Business Analysts

1. **Study** `sales_workflow.md` for sales process understanding
2. **Review** `inventory_workflow.md` for stock management
3. **Reference** `database_schema.md` for data relationships

### For Quality Assurance

1. **Use** workflow diagrams to create test scenarios
2. **Reference** business rules in each workflow
3. **Verify** error handling flows
4. **Test** edge cases documented in flows

## Diagram Legend

### Flowchart Symbols

- `[()]` - Start/End points (rounded rectangles)
- `[ ]` - Process steps (rectangles)
- `{ }` - Decision points (diamonds)
- `-->` - Flow direction (arrows)
- `-.->` - Alternate flow (dotted arrows)

### Sequence Diagram Symbols

- `actor` - External user or system
- `participant` - System component
- `-->` - Synchronous message
- `-->` - Return message
- `Note over` - Comments or annotations
- `loop` - Repetition block
- `alt` - Alternative paths

### ER Diagram Symbols

- `||--o{` - One-to-many relationship
- `}|--||` - Many-to-one relationship
- `>>` - Inheritance
- `PK` - Primary Key
- `FK` - Foreign Key
- `UK` - Unique Key

## Viewing the Diagrams

### GitHub/GitLab
All diagrams use **Mermaid** syntax which renders automatically in:
- GitHub README and Markdown files
- GitLab Markdown files
- Bitbucket Markdown files
- Many other Markdown viewers

### VS Code
Install the **Mermaid Preview** extension:
1. Open a Markdown file
2. Press `Ctrl+Shift+V` (or `Cmd+Shift+V` on Mac)
3. Diagrams render inline

### Online Viewers
- [Mermaid Live Editor](https://mermaid.live/) - Copy/paste Mermaid code
- [Mermaid Diagram GitHub](https://mermaid-js.github.io/mermaid-live-editor/) - Official editor

### Exporting to Images
Use the Mermaid Live Editor to:
1. Copy diagram code from any `.md` file
2. Paste into the editor
3. Export as PNG, SVG, or PDF

## Document Conventions

### Naming Conventions
- **Tables/Models**: `PascalCase` (e.g., `Sale`, `Customer`)
- **Columns/Fields**: `snake_case` (e.g., `sale_date`, `customer_id`)
- **Functions/Methods**: `snake_case` (e.g., `create_sale`, `get_product`)
- **Variables**: `snake_case` (e.g., `sale_id`, `total_amount`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_LOGIN_ATTEMPTS`)

### Status Codes
- **Success**: `(True, None, data)`
- **Failure**: `(False, error_message, None)`
- **Partial**: `(True, warning_message, data)`

### HTTP Status Codes (Future API)
- **200 OK** - Successful request
- **400 Bad Request** - Validation error
- **401 Unauthorized** - Not authenticated
- **403 Forbidden** - No permission
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Business rule violation
- **500 Internal Server Error** - Server error

## Related Documentation

- **[SETUP.md](../../SETUP.md)** - Installation and configuration guide
- **[CLAUDE.md](../../CLAUDE.md)** - Development guidelines
- **[REVIEW_SUMMARY.md](../../REVIEW_SUMMARY.md)** - System review and improvement plan
- **[app/config.py](../../app/config.py)** - Configuration management
- **[app/settings.py](../../app/settings.py)** - Business settings groups

## Contributing

When adding new features or workflows:

1. **Update relevant diagrams** in this directory
2. **Follow Mermaid syntax** standards
3. **Include error flows** for all processes
4. **Document business rules** explicitly
5. **Add sequence diagrams** for complex interactions
6. **Update this README** with new diagrams

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-03-14 | Initial documentation with all 5 core diagrams |

## Support

For questions about these diagrams:
- Review the specific diagram document
- Check [CLAUDE.md](../../CLAUDE.md) for development context
- Consult [REVIEW_SUMMARY.md](../../REVIEW_SUMMARY.md) for architecture decisions
- Open an issue on GitHub

---

**Document Version:** 1.0
**Last Updated:** 2025-03-14
**ERP Paraguay Version:** 6.0.0
