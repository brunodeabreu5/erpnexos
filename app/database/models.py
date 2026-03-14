
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, func, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from app.database.db import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """User model for authentication and authorization.

    Attributes:
        id: Primary key
        username: Unique username for login
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        email: User's email address
        role: User role (admin, manager, sales, viewer)
        last_login: Timestamp of last login
        is_active: Whether the user account is active
        created_at: Timestamp of user creation
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    role = Column(String(50), default='sales', nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    audit_logs = relationship("AuditLog", backref="user")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password.

        Args:
            plain_password: The plain text password to verify
            hashed_password: The bcrypt hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Bcrypt accepts at most 72 bytes; longer passwords are truncated.

        Args:
            password: The plain text password to hash

        Returns:
            The bcrypt hashed password
        """
        encoded = password.encode("utf-8")
        if len(encoded) > 72:
            password = encoded[:72].decode("utf-8", errors="ignore")
        return pwd_context.hash(password)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Customer(Base):
    """Customer model for sales and CRM.

    Attributes:
        id: Primary key
        name: Customer name
        email: Unique email address
        phone: Contact phone number
        address: Customer address
        tax_id: Tax identification (RUC/CI)
        balance: Account balance for credit sales
        is_active: Whether the customer is active
        created_at: Timestamp of customer creation
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), unique=True, nullable=True)
    balance = Column(Numeric(12, 2), default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', balance={self.balance})>"

    # Indexes for common queries
    __table_args__ = (
        Index('idx_customer_active', 'is_active', 'created_at'),
    )


class Category(Base):
    """Category model for product organization.

    Attributes:
        id: Primary key
        name: Unique category name
        description: Category description
        is_active: Whether the category is active
        created_at: Timestamp of category creation
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Product model for inventory management.

    Attributes:
        id: Primary key
        name: Product name
        sku: Unique stock keeping unit
        price: Unit selling price
        cost_price: Unit cost price for profit margin calculation
        stock: Current stock quantity
        reorder_point: Stock level to trigger reorder
        is_active: Whether the product is active
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(50), unique=True, nullable=True, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Numeric(10, 2), nullable=False, default=0)
    reorder_point = Column(Numeric(10, 2), default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    category = relationship("Category", backref="products")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"

    # Indexes for common queries
    __table_args__ = (
        Index('idx_product_active', 'is_active', 'created_at'),
        Index('idx_product_category', 'category_id', 'is_active'),
    )


class Sale(Base):
    """Sale model for sales transactions.

    Attributes:
        id: Primary key
        customer_id: Foreign key to customer
        sale_date: Date and time of sale
        subtotal: Subtotal before tax and discount
        tax_amount: Tax amount calculated
        discount_amount: Discount amount applied
        total: Final total amount
        payment_method: Payment method (cash, transfer, card)
        payment_status: Payment status (pending, paid, cancelled)
        notes: Additional notes
        status: Sale status (completed, cancelled)
        created_at: Timestamp of record creation
    """
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), default='pending', nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default='completed', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    items = relationship("SaleItem", backref="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", backref="sale", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_sale_customer_date', 'customer_id', 'sale_date'),
        Index('idx_sale_status_date', 'status', 'sale_date'),
    )

    def __repr__(self) -> str:
        return f"<Sale(id={self.id}, customer_id={self.customer_id}, total={self.total})>"


class SaleItem(Base):
    """Sale item model for individual line items in a sale.

    Attributes:
        id: Primary key
        sale_id: Foreign key to sale
        product_id: Foreign key to product
        quantity: Quantity sold
        unit_price: Price per unit at time of sale
        subtotal: Subtotal for this line (quantity * unit_price)
        discount: Discount amount for this line
        total: Final total for this line (subtotal - discount)
    """
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    # Relationship
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<SaleItem(id={self.id}, sale_id={self.sale_id}, product_id={self.product_id}, quantity={self.quantity})>"


class Payment(Base):
    """Payment model for sale payments.

    Attributes:
        id: Primary key
        sale_id: Foreign key to sale
        payment_date: Date and time of payment
        amount: Payment amount
        payment_method: Payment method (cash, transfer, card)
        reference: Reference number (check number, transaction ID, etc.)
        notes: Additional notes
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False, index=True)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, sale_id={self.sale_id}, amount={self.amount})>"


class AuditLog(Base):
    """Audit log model for tracking user actions.

    Attributes:
        id: Primary key
        user_id: Foreign key to user who performed the action
        action: Action performed (create_sale, delete_product, etc.)
        entity_type: Type of entity affected (Sale, Product, Customer, etc.)
        entity_id: ID of the affected entity
        old_values: Previous values (for updates/deletes)
        new_values: New values (for creates/updates)
        created_at: Timestamp of the action
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', entity_type='{self.entity_type}')>"


class Supplier(Base):
    """Supplier model for purchase management.

    Attributes:
        id: Primary key
        name: Supplier name
        contact_person: Name of contact person
        email: Supplier email
        phone: Contact phone number
        address: Supplier address
        tax_id: Tax identification (RUC/CI)
        is_active: Whether the supplier is active
    """
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    purchases = relationship("Purchase", backref="supplier")

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name='{self.name}')>"


class Purchase(Base):
    """Purchase model for tracking purchases from suppliers.

    Attributes:
        id: Primary key
        supplier_id: Foreign key to supplier
        purchase_date: Date of purchase
        subtotal: Subtotal before tax
        total: Total including tax
        status: Purchase status (pending, received, cancelled)
        notes: Additional notes
    """
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    items = relationship("PurchaseItem", backref="purchase", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Purchase(id={self.id}, supplier_id={self.supplier_id}, total={self.total})>"


class PurchaseItem(Base):
    """Purchase item model for individual line items in a purchase.

    Attributes:
        id: Primary key
        purchase_id: Foreign key to purchase
        product_id: Foreign key to product
        quantity: Quantity purchased
        unit_cost: Cost per unit
        subtotal: Subtotal for this line (quantity * unit_cost)
    """
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    # Relationships
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<PurchaseItem(id={self.id}, purchase_id={self.purchase_id}, product_id={self.product_id}, quantity={self.quantity})>"


class Expense(Base):
    """Expense model for tracking business expenses.

    Attributes:
        id: Primary key
        category: Expense category (rent, utilities, salaries, taxes, materials, other)
        amount: Expense amount
        description: Description of the expense
        expense_date: Date when the expense occurred
        payment_method: How it was paid (cash, transfer, card, check)
        reference: Reference number (invoice number, receipt number, etc.)
        created_at: Timestamp of record creation
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=False)
    expense_date = Column(DateTime(timezone=True), nullable=False, index=True)
    payment_method = Column(String(50), nullable=True)
    reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, category='{self.category}', amount={self.amount}, expense_date={self.expense_date})>"

    # Indexes for common queries
    __table_args__ = (
        Index('idx_expense_category_date', 'category', 'expense_date'),
        Index('idx_expense_date', 'expense_date'),
    )
