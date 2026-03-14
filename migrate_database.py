"""Database migration script to update schema for ERP Paraguay V6.

This script updates the database schema to match the new models:
- products.sku → products.barcode
- products.price → products.sale_price
- Add missing columns and indexes

Run this after updating to V6.0 to migrate your existing database.
"""
import sys
from sqlalchemy import text
from app.database.db import engine


def migrate_database():
    """Migrate database to V6 schema."""
    print("Starting database migration to V6.0...")

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        try:
            # Check if products table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'products'
                )
            """))
            if not result.scalar():
                print("Products table doesn't exist yet. Will be created automatically.")
                trans.commit()
                return

            # Get current columns in products table
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'products'
                ORDER BY ordinal_position
            """))
            existing_columns = [row[0] for row in result]
            print(f"Existing columns: {existing_columns}")

            # Migration 1: Rename 'sku' to 'barcode' if it exists
            if 'sku' in existing_columns and 'barcode' not in existing_columns:
                print("Renaming 'sku' column to 'barcode'...")
                conn.execute(text("ALTER TABLE products RENAME COLUMN sku TO barcode"))
                print("[OK] Renamed sku to barcode")
            elif 'barcode' in existing_columns:
                print("[OK] barcode column already exists")
            else:
                print("[WARNING] Neither sku nor barcode found - adding barcode column")
                conn.execute(text("ALTER TABLE products ADD COLUMN barcode VARCHAR(50) UNIQUE"))

            # Migration 2: Rename 'price' to 'sale_price' if it exists
            if 'price' in existing_columns and 'sale_price' not in existing_columns:
                print("Renaming 'price' column to 'sale_price'...")
                conn.execute(text("ALTER TABLE products RENAME COLUMN price TO sale_price"))
                print("[OK] Renamed price to sale_price")
            elif 'sale_price' in existing_columns:
                print("[OK] sale_price column already exists")
            else:
                print("[WARNING] Neither price nor sale_price found - adding sale_price column")
                conn.execute(text("ALTER TABLE products ADD COLUMN sale_price NUMERIC(10, 2)"))

            # Migration 3: Add reorder_point if missing
            if 'reorder_point' not in existing_columns:
                print("Adding 'reorder_point' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN reorder_point NUMERIC(10, 2) DEFAULT 10"))
                print("[OK] Added reorder_point")
            else:
                print("[OK] reorder_point column already exists")

            # Migration 4: Add description if missing
            if 'description' not in existing_columns:
                print("Adding 'description' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN description TEXT"))
                print("[OK] Added description")
            else:
                print("[OK] description column already exists")

            # Migration 5: Add supplier_id if missing
            if 'supplier_id' not in existing_columns:
                print("Adding 'supplier_id' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)"))
                print("[OK] Added supplier_id")
            else:
                print("[OK] supplier_id column already exists")

            # Migration 6: Add updated_at column if missing
            if 'updated_at' not in existing_columns:
                print("Adding 'updated_at' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))
                print("[OK] Added updated_at")
            else:
                print("[OK] updated_at column already exists")

            # Migration 7: Add cost_price if missing
            if 'cost_price' not in existing_columns:
                print("Adding 'cost_price' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN cost_price NUMERIC(10, 2)"))
                print("[OK] Added cost_price")
            else:
                print("[OK] cost_price column already exists")

            # Migration 8: Add is_active if missing
            if 'is_active' not in existing_columns:
                print("Adding 'is_active' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                print("[OK] Added is_active")
            else:
                print("[OK] is_active column already exists")

            # Migration 9: Add created_at if missing
            if 'created_at' not in existing_columns:
                print("Adding 'created_at' column...")
                conn.execute(text("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
                print("[OK] Added created_at")
            else:
                print("[OK] created_at column already exists")

            # Migration 10: Add category_id if missing
            if 'category_id' not in existing_columns:
                print("Adding 'category_id' column...")
                # First check if categories table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'categories'
                    )
                """))
                if result.scalar():
                    conn.execute(text("ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id)"))
                    print("[OK] Added category_id with foreign key")
                else:
                    conn.execute(text("ALTER TABLE products ADD COLUMN category_id INTEGER"))
                    print("[OK] Added category_id without foreign key (categories table doesn't exist yet)")
            else:
                print("[OK] category_id column already exists")

            # Commit transaction
            trans.commit()
            print("\n[OK] Database migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            print("Rolling back changes...")
            sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("ERP Paraguay V6 - Database Migration")
    print("=" * 60)
    print()

    migrate_database()

    print()
    print("Next steps:")
    print("1. Run the application: python main.py")
    print("2. The database will be fully initialized with new schema")
    print("=" * 60)
