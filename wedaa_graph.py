# billing_agent.py

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from sqlorm import *
from database import *
from pydantic import BaseModel, Field, ConfigDict,ValidationError
from typing import Optional, List, Dict
from datetime import datetime
import json
import random
from mongo import mongo_orders_collection
import asyncio
from bill import generate_invoice_image


async def check_customer(phone_number: str):
    session = SessionLocal()
    try:
        customer = await asyncio.to_thread(lambda: session.query(Customers).filter_by(phone_number=phone_number).first())
        if customer:
            print(f"Customer: {customer.name}, Phone: {customer.phone_number}, Address: {customer.address}")
            return customer
        else:
            return False
    except Exception as e:
        return f"❌ Error: {e}"
    finally:
        session.close()

async def get_prices():
    def _prices():
        return [
            {"item_id": "item001", "name": "Groundnut Oil", "unit": "litre", "price_per_unit": 300.0},
            {"item_id": "item002", "name": "Coconut Oil", "unit": "litre", "price_per_unit": 400.0},
            {"item_id": "item003", "name": "Sesame Oil", "unit": "litre", "price_per_unit": 450.0}
        ]
    return await asyncio.to_thread(_prices)

# Step 3: Generate invoice using LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)


class OrderItem(BaseModel):
    item_name: str
    quantity: int
    units: str
    price_per_unit: Optional[float] = None
    total_price: Optional[float] = None

class Order(BaseModel):
    phone_number: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    customer_name: Optional[str] = None
    address: Optional[str] = None
    maps_link: Optional[str] = None
    purchase_type: str = "instore"  # "delivery" or "instore"
    order_placed_at: datetime = Field(default_factory=datetime.now)
    items: List[OrderItem] = Field(default_factory=list)
    order_total: Optional[float] = None
    customer_id: Optional[int] = None
    order_num: Optional[int] = None

class CustomerSchema(BaseModel):
    id: int
    name: str
    phone_number: str
    address: str
    google_maps_link: str | None = None  # Optional field

    model_config = ConfigDict(from_attributes=True)


async def add_sql_order(order: 'Order'):
    session = SessionLocal()
    try:
        def _add():
            new_order = OrderSummary(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                num_items=len(order.items),
                purchase_type=order.purchase_type,
                order_placed_at=order.order_placed_at,
                order_total=order.order_total
            )
            session.add(new_order)
            session.commit()
            session.refresh(new_order)
            return new_order.order_num
        return await asyncio.to_thread(_add)
    except Exception as e:
        session.rollback()
        raise Exception(f"SQL Insert Error: {e}")
    finally:
        session.close()

async def store_order(state: dict):
    order = Order(**state)
    order_num = await add_sql_order(order)
    order.order_num = order_num
    state["order_num"] = order_num
    await asyncio.to_thread(mongo_orders_collection.insert_one, order.model_dump())
    return state

async def generate_invoice(state: dict):
    """
    Generates an invoice image using the bill.py logic.
    """
    print("[DEBUG] Starting generate_invoice")
    try:
        order = Order(**state)
        fields = {
            "Name": order.customer_name or "",
            "Order Number": str(order.order_num or ""),
            "Date": order.order_placed_at.strftime("%Y-%m-%d") if order.order_placed_at else "",
            "Phone": order.phone_number,
            "Bill Number": f"BILL-{order.order_num or 'XXXX'}",
            "Address": order.address or ""
        }
        table_data = []
        total_amount = 0.0
        for idx, item in enumerate(order.items, 1):
            price = item.price_per_unit or 0.0
            amount = item.total_price or (price * (item.quantity or 0))
            table_data.append([
                str(idx),
                item.item_name,
                str(item.quantity),
                f"₹{price:.2f}",
                f"₹{amount:.2f}"
            ])
            total_amount += amount

        # Do not specify output_path, let bill.py handle it dynamically
        await asyncio.to_thread(
            generate_invoice_image,
            logo_path="wedaa_logo_aw.png",
            watermark_path="wedaa_logo_circle_aw.png",
            fields=fields,
            table_data=table_data
        )
        print(f"[DEBUG] Invoice generated (dynamic path handled in bill.py)")
        return {
            "invoice_path": None,
            "total_amount": total_amount,
            "order_num": order.order_num,
            "bill_generated": True
        }
    except Exception as e:
        print(f"[ERROR] generate_invoice failed: {e}")
        return {
            "invoice_path": None,
            "total_amount": None,
            "order_num": state.get("order_num"),
            "bill_generated": False,
            "error": str(e)
        }

async def format_output(state: dict):
    bill_generated = state.get("bill_generated", False)
    return {
        "message": f"✅ Order successfully stored. Total: ₹{state['order_total']}",
        "order_num": state['order_num'],
        "delivery": state['purchase_type'] == "delivery",
        "bill_generated": bill_generated
    }

async def calculate_total(state: dict):
    total = sum(item['quantity'] * item['price_per_unit'] for item in state['items'])
    state['order_total'] = total
    return state

async def order_agent(order: Order, user_input: str, llm):
    phone_number = order.phone_number
    customer = await check_customer(phone_number)
    if customer:
        customer_schema = CustomerSchema.model_validate(customer)
        cust_json = customer_schema.model_dump_json()
    else:
        cust_json = '{}'

    price_list = await get_prices()
    price_list_json = json.dumps(price_list)

    order.messages.append({"role": "user", "content": user_input})
    order_data_json = order.model_dump_json(exclude_none=True, exclude_defaults=True, indent=2)

    prompt = ChatPromptTemplate.from_template("""
                        You are an order assistant. Use the customer_info and price_list below to assist the customer in placing an order.

                        Customer info (in JSON format):
                        {cust_json}

                        Price list (in JSON format):
                        {price_list_json}

                        User message:
                        {user_message}

                        Instructions:
                        1. Check if the customer exists based on `phone_number` and the provided `customer_info`. If not, assume it's a new customer and ask for any missing details (e.g., name, address, delivery/pickup, etc.).
                        2. Use the provided `price_list` to determine item prices and update in the JSON object.
                        3. Extract the complete order and return ONLY a JSON object that matches the following Python Pydantic class schema (all required and optional fields must be present, even if null/empty):

                        class Order(BaseModel):
                            phone_number: str
                            messages: List[Dict[str, str]]
                            customer_name: Optional[str]
                            address: Optional[str]
                            maps_link: Optional[str]
                            purchase_type: str
                            order_placed_at: str
                            items: List[OrderItem]
                            order_total: Optional[float]
                            customer_id: Optional[int]
                            order_num: Optional[int]

                        class OrderItem(BaseModel):
                            item_name: str
                            quantity: int
                            units: str
                            price_per_unit: Optional[float]
                            total_price: Optional[float]

                        - Calculate the total price for each item and the total order price and include them in the JSON.
                        - Do NOT include any additional text or explanation, only the JSON object.
                        """)

    formatted_prompt = prompt.format_messages(
        cust_json=cust_json,
        price_list_json=price_list_json,
        user_message=user_input.strip()
    )
    response = await asyncio.to_thread(llm.invoke, formatted_prompt)
    assistant_message = response.content
    try:
        completed_order_json = json.loads(assistant_message)
        if not completed_order_json.get("order_placed_at"):
            random_time = datetime.utcnow().replace(hour=random.randint(0, 23), minute=random.randint(0, 59), second=random.randint(0, 59))
            completed_order_json["order_placed_at"] = random_time.isoformat()
        completed_order = Order.model_validate(completed_order_json)
        return completed_order
    except (json.JSONDecodeError, ValidationError) as e:
        print("❌ Failed to parse or validate:", e)
        return order

async def verify_order_prices(order_json: dict) -> dict:
    prices = await get_prices()
    price_lookup = {item["name"].lower(): item["price_per_unit"] for item in prices}
    items = order_json.get("items", [])
    calculated_total = 0.0
    for item in items:
        name = item.get("item_name", "").lower()
        quantity = item.get("quantity", 0)
        expected_price = price_lookup.get(name)
        if expected_price is None:
            print(f"❌ Unknown item: {name}")
            continue
        if abs(item.get("price_per_unit", 0.0) - expected_price) > 0.01:
            print(f"⚠️ Correcting price per unit for {name}: {item.get('price_per_unit')} -> {expected_price}")
            item["price_per_unit"] = expected_price
        expected_total = expected_price * quantity
        if abs(item.get("total_price", 0.0) - expected_total) > 0.01:
            print(f"⚠️ Correcting total price for {name}: {item.get('total_price')} -> {expected_total}")
            item["total_price"] = expected_total
        calculated_total += expected_total
    if abs(order_json.get("order_total", 0.0) - calculated_total) > 0.01:
        print(f"⚠️ Correcting order total: {order_json.get('order_total')} -> {calculated_total}")
        order_json["order_total"] = calculated_total
    return order_json

async def process_order_pipeline(order: Order, user_input: str, llm):
    print("[INFO] Starting process_order_pipeline")
    try:
        print("[INFO] Calling order_agent")
        completed_order = await order_agent(order, user_input, llm)
        print("[INFO] order_agent completed")
    except Exception as e:
        print(f"[ERROR] order_agent failed: {e}")
        return {"error": f"order_agent failed: {e}"}
    try:
        print("[INFO] Calling verify_order_prices")
        order_json = completed_order.model_dump()
        verified_order_json = await verify_order_prices(order_json)
        print("[INFO] verify_order_prices completed")
    except Exception as e:
        print(f"[ERROR] verify_order_prices failed: {e}")
        return {"error": f"verify_order_prices failed: {e}"}
    try:
        print("[INFO] Calling store_order")
        await store_order(verified_order_json)
        print("[INFO] store_order completed")
    except Exception as e:
        print(f"[ERROR] store_order failed: {e}")
        return {"error": f"store_order failed: {e}"}
    try:
        print("[INFO] Calling generate_invoice")
        invoice_result = await generate_invoice(verified_order_json)
        print("[INFO] generate_invoice completed")
        # Merge invoice result into state for format_output
        verified_order_json.update(invoice_result)
    except Exception as e:
        print(f"[ERROR] generate_invoice failed: {e}")
        verified_order_json["bill_generated"] = False
    try:
        print("[INFO] Calling format_output")
        output = await format_output(verified_order_json)
        print("[INFO] format_output completed")
        return output
    except Exception as e:
        print(f"[ERROR] format_output failed: {e}")
        return {"error": f"format_output failed: {e}"}

# Example usage:
async def main():
    empty_order = Order(phone_number="9876054321")
    user_input = "I want 2 litres of groundnut oil, and two litres of sesame oil."
    result = await process_order_pipeline(empty_order, user_input, llm)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())


