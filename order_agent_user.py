from wedaa_graph import billing_graph, get_prices, OrderItem, Order
from datetime import datetime

def order_agent_cli():
    print("=== Welcome to the Order CLI ===")
    phone = input("📞 Enter phone number: ").strip()
    name = input("👤 Enter customer name: ").strip()
    purchase_type = input("🛒 Purchase type (delivery / instore): ").strip().lower()

    address = maps_link = None
    if purchase_type == "delivery":
        address = input("🏠 Enter delivery address: ").strip()
        maps_link = input("🗺️ Enter Google Maps link (optional): ").strip()

    # Price list lookup
    prices = get_prices()
    price_lookup = {item["item_id"]: item for item in prices}

    # Collect items
    items = []
    print("\n🧾 Enter items (type 'done' to finish):")
    while True:
        item_id = input("🔢 Item ID: ").strip()
        if item_id.lower() == "done":
            break
        if item_id not in price_lookup:
            print("❌ Invalid item ID.")
            continue
        try:
            qty = float(input("📦 Quantity: ").strip())
        except ValueError:
            print("❌ Invalid quantity.")
            continue
        item = price_lookup[item_id]
        items.append(OrderItem(
            item_id=item_id,
            quantity=qty,
            price_per_unit=item["price_per_unit"]
        ))

    # Create Order state
    order = Order(
        phone_number=phone,
        customer_name=name,
        purchase_type=purchase_type,
        address=address,
        maps_link=maps_link,
        items=items,
        order_placed_at=datetime.now()
    )

    # Invoke LangGraph
    result = billing_graph.invoke(order.dict())
    print("\n✅ Order Processed:")
    print(result)

if __name__ == "__main__":
    order_agent_cli()
