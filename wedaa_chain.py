from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from functions import *
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from mongo import *
import json 
from langgraph.prebuilt import create_react_agent, chat_agent_executor
from langchain_openai import ChatOpenAI
from langchain_community.tools import Tool  # (if you use Tool class)
import os


load_dotenv()

class OrderItem(BaseModel):
    item_name: str
    quantity: int
    units: str
    price_per_unit: Optional[float] = None
    total_price: Optional[float] = None

class Order(BaseModel):
    phone_number: str
    customer_name: Optional[str] = None
    address: Optional[str] = None
    maps_link: Optional[str] = None
    purchase_type: str = "instore"  # "delivery" or "instore"
    order_placed_at: datetime = Field(default_factory=datetime.now)
    items: List[OrderItem] = Field(default_factory=list)
    order_total: Optional[float] = None
    customer_id: Optional[int] = None
    order_num: Optional[int] = None

tools = [
    Tool(name="insert_order_sql", func=insert_order_sql, description="Insert order into SQL"),
    Tool(name="add_customer", func=add_customer, description="Add customer to Custoomer table")
]
model = ChatOpenAI(temperature=0.6)
agent = create_react_agent(model, tools)
ph_number = 9876543210

def order_agent(user_input:str):
    
    customer = check_customer(ph_number)
    cust_json = json.dumps(customer)

    price_list = get_prices()
    price_list_json=json.dumps(price_list)

    system_prompt = f"""You are a helpful order processing assistant for Wedaa bioproducts ltd.
                        You should converse with a customer to record and process their order.

                        price_list:
                        {price_list_json}
                        customer_info:
                        {cust_json}
 
                        Extract the item information from the conversation and format it as json like-

                        order_data:{{
                        "phone_number": "",
                        "customer_name": null,
                        "address": null,
                        "maps_link": null,
                        "purchase_type": "instore",
                        "order_placed_at": "2025-04-27T12:00:00",
                        "items": [],
                        "order_total": null,
                        "customer_id": null,
                        "order_num": null
                        }}
                        
                        order_summary: {{
                        "order_num": "integer",
                        "customer_id": "integer",
                        "customer_name": "string",
                        "num_items": "integer",
                        "purchase_type": "string",  // expected: "delivered" or "instore"
                        "order_placed_at": "string",  // ISO 8601 datetime format, e.g. "2025-05-02T14:30:00Z"
                        "order_total": "number"
                        }}

                        Create order summary and insert into sql with insert_order_sql
                        Fill the details of the customer from the customer info given above.
                        if customer info is empty, you are conversing with a new customer. Ask if the customer wants delivery or not. 
                        If delivery,Get these details from the customer:
                        - Name, address for delivery and maps link to make it easier. 
                        For links, if customer says ignore, ignore it. 

                        Add the customer table and fill the customer details in order_data 

                        based on the prices in price_list, calculate the order total amount and add it in the json format.

                        """

    conversation_history = [
        {"role": "system", "content": system_prompt},  # Add system prompt here
    ]

    while True:
        input("You: ")
        conversation_history.append({"role": "user", "content": user_input})
        
        response = agent.invoke(input={"messages": conversation_history})

        # Extract agent's message
        messages = response.get('messages', [])
        if messages:
            last_message = messages[-1]
            ai_message = last_message.content  # access the .content attribute
        else:
            ai_message = ""
        print(f"Assistant: {ai_message}")

        conversation_history.append({"role": "assistant", "content": ai_message})

        # Check if the AI has completed the order
        if is_order_complete(ai_message):
            break

def is_order_complete(ai_message):
    # Simple version: if AI message contains final JSON (with "phone_number", "items", etc.), consider it complete
    if "phone_number" in ai_message and "items" in ai_message:
        return True
    return False


user_input = input("Pls type your order:")
print(order_agent(user_input))