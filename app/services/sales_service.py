
from app.database.db import SessionLocal
from app.database.models import Product

def list_products():
    db = SessionLocal()
    return db.query(Product).all()
