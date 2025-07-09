# mongo_models.py
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB client setup
mongo_uri = os.getenv("MONGODB_URI")
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client["wedaa_db"]
mongo_orders_collection = mongo_db["orders"]
mongo_prices_collection = mongo_db["prices"]
# Pydantic model for items
class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    unit: str
    price_per_unit: float

# Pydantic model for Mongo order
class MongoOrder(BaseModel):
    order_num: int
    customer_id: int
    customer_name: str
    items: List[OrderItem]
    purchase_type: Literal["delivered", "instore"]
    order_placed_at: datetime
    order_total: float

def insert_order_to_mongo(order: MongoOrder):
    mongo_orders_collection.insert_one(order.dict())


def get_prices():
    price_list = []
    
    prices = mongo_prices_collection.find()
    for price in prices:
        price_list.append(price)
    
    return price_list

    