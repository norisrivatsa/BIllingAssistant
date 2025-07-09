# from sqlalchemy import Column, Integer, String, create_engine, DateTime , ForeignKey, Text
# from sqlalchemy.orm import declarative_base, sessionmaker, relationship ,Session
# from sqlalchemy.exc import IntegrityError
# from dotenv import load_dotenv
# import os
# from datetime import datetime
# import pytz



# load_dotenv()

# IST = pytz.timezone('Asia/Kolkata')
# ist_now = datetime.now(IST)
# Base = declarative_base()

# db = os.getenv("DATABASE_URL")

# class Orders(Base):
#     __tablename__ = 'Orders'

#     order_num = Column(String(20), primary_key=True)
#     date = Column(DateTime(timezone=True), nullable= False) 
#     cust_name = Column(String(50), nullable=False)
#     cust_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
#     item = Column(String(50), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     units = Column(String(10), nullable=False)
#     price_per_unit = Column(Integer, nullable=False)
#     item_id = Column(String(15), nullable=False,)      
#     tot_amount = Column(Integer, nullable=False)

#     customer = relationship("Customer", backref="orders")  

# class Customer(Base):
#     __tablename__ = "customers"

#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     phone_number = Column(String(20), nullable=False, unique=True)
#     address = Column(Text, nullable=True)  # Allows long addresses
#     google_maps_link = Column(Text, nullable=True)  # Stores the location link


# # Create engine once
# engine = create_engine(db)

# # Create a new sessionmaker factory
# SessionLocal = sessionmaker(bind=engine)


# Base.metadata.create_all(engine)

# def get_session():
#     """
#     Returns a new SQLAlchemy session instance.
#     Each call creates a fresh session.
#     """
#     return SessionLocal()

# def add_new_order(customer_data: dict, order_data: dict):
#     """
#     Adds a new order with a temporary customer. The customer is added to the database first.
    
#     :param session: The SQLAlchemy session
#     :param customer_data: A dictionary containing customer details (e.g., name, phone_number, address)
#     :param order_data: A dictionary containing order details (e.g., item, quantity, price_per_unit)
#     :return: The newly added order's ID
#     """
#     session = get_session()
#     try:
#         # Create a temporary customer
#         temp_customer = Customer(
#             name=customer_data['name'],
#             phone_number=customer_data['phone_number'],
#             address=customer_data['address'],
#             google_maps_link=customer_data['google_maps_link']  # Optional field
#         )

#         # Add customer to the session and commit to get the customer ID
#         session.add(temp_customer)
#         session.commit()

#         # Create an order with the temp customer's ID
#         new_order = Orders(
#             date=datetime.now(),
#             cust_id=temp_customer.id,
#             item=order_data['item'],
#             quantity=order_data['quantity'],
#             units=order_data['units'],
#             price_per_unit=order_data['price_per_unit'],
#             item_id=order_data['item_id'],
#             tot_amount=order_data['quantity'] * order_data['price_per_unit']
#         )

#         # Add the order to the session
#         session.add(new_order)
#         session.commit()

#         # Return the newly created order ID
#         return new_order.order_num

#     except IntegrityError:
#         session.rollback()  # Rollback in case of integrity error (e.g., unique constraint violation)
#         raise
#     except Exception as e:
#         session.rollback()  # Rollback for any other exceptions
#         print(f"An error occurred: {e}")
#         raise

# sql_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime
from sqlorm import *

load_dotenv()


# Setup SQL engine and session
sql_db_url = os.getenv("DATABASE_URL")
engine = create_engine(sql_db_url)
SessionLocal = sessionmaker(bind=engine)



# def check_customer(phone_number: str):
#     session = SessionLocal()
#     try:
#         # Query to find customer by name and phone number
#         customer = session.query(Customers).filter_by(phone_number=phone_number).first()

#         # If customer exists, return customer_id
#         if customer:
#             print(f"Customer: {customer.name}, Phone: {customer.phone_number}, Address: {customer.address}")
#             return customer
#         else:
#             return False

#     except Exception as e:
#         return f"❌ Error: {e}"
#     finally:
#         session.close()

# ph_number = "9876054321"
# result = check_customer(ph_number)
# print(result)