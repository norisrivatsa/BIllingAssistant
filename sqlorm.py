from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

class OrderSummary(Base):
    __tablename__ = 'order_summary'

    order_num = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False)
    customer_name = Column(String(255), nullable=False)
    num_items = Column(Integer, nullable=False)
    purchase_type = Column(String(20), nullable=False)  # 'delivered' or 'instore'
    order_placed_at = Column(DateTime, nullable=False)
    order_total = Column(Float, nullable=False)


class Customers(Base):
    __tablename__ = 'Customers'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)  # Auto-incrementing customer ID
    name = Column(String(255), nullable=False)  # Customer name
    phone_number = Column(String(20), nullable=False, unique=True)  # Phone number (unique)
    address = Column(String(500), nullable=False)  # Customer address
    google_maps_link = Column(String(500), nullable=True)  # Link to the address on Google Maps