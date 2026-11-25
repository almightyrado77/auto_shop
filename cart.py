from decimal import Decimal


def build_cart(cart_session, products):
    """Сглобява редовете на количката и общата сума от данните в базата."""
    items = []
    total = Decimal("0")

    for product_id, quantity in cart_session.items():
        product = products.get(int(product_id))
        if product is None:
            continue  # продуктът е изтрит от каталога

        price = Decimal(str(product["price"]))
        subtotal = price * quantity
        items.append({
            "id": product["id"],
            "name": product["name"],
            "price": price,
            "stock": product["stock"],
            "quantity": quantity,
            "subtotal": subtotal,
        })
        total += subtotal

    return items, total