from langchain.agents import tool
from langchain_community.tools import Tool 
from database import *    # session factory
from sqlalchemy.orm import Session
from sqlorm import *


def insert_order_sql(order_data: dict):
    """
    Use this tool to add order to SQL database
    """
    if isinstance(order_data, str):
        order_data = json.loads(order_data)
    session = SessionLocal()
    try:
        new_summary = OrderSummary(
            customer_id=order_data["customer_id"],
            customer_name=order_data["customer_name"],
            num_items=order_data["num_items"],
            purchase_type=order_data["purchase_type"],
            order_placed_at=order_data["order_placed_at"],
            order_total=order_data["order_total"],
        )
        session.add(new_summary)
        session.commit()
        return f"Order for {order_data['customer_name']} inserted successfully."
    except Exception as e:
        session.rollback()
        print(f"Failed to insert order summary: {e}")
        return f"Failed to insert order: {str(e)}"
        raise
    finally:
        session.close()



# Function to add a new customer
def add_customer(name: str, phone_number: str, address: str, google_maps_link: str):
    """
    Use this function to add a customer to customerr table
    """
    session = SessionLocal()
    try:
        # Insert the new customer into the SQL database
        new_customer = Customers(
            customer_name=name,
            phone_number=phone_number,
            address=address,
            maps_link=google_maps_link
        )
        session.add(new_customer)
        session.commit()  # Commit the new customer to the database
        session.refresh(new_customer)  # Ensure full object is loaded with customer_id

        # Return the customer
        return new_customer
    except Exception as e:
        raise Exception(f"❌ Failed to add customer: {str(e)}")
    finally:
        session.close()

def get_cust_name(customer_id : str):
    session = SessionLocal()
    try:
        customer = session.query(Customers).filter(
            Customers.customer_id == customer_id,
        ).first()
        if customer:
            return customer.customer_name
        else:
            return False
    except Exception as e:
        return f"❌ Error: {e}"
    finally:
        session.close()
        


def check_customer(phone_number: str):
    session = SessionLocal()
    try:
        # Query to find customer by name and phone number
        customer = session.query(Customers).filter_by(phone_number=phone_number).first()

        # If customer exists, return customer_id
        if customer:
            return customer
        else:
            return False

    except Exception as e:
        return f"❌ Error: {e}"
    finally:
        session.close()
