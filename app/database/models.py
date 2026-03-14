
from sqlalchemy import Column,Integer,String,Numeric
from app.database.db import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True)
    name = Column(String)
    price = Column(Numeric)
    stock = Column(Numeric)
