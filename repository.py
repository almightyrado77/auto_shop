from decimal import Decimal
from db import get_connection
import oracledb

def get_categories():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY name")
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]


def get_products(category_id=None):
    sql = """
        SELECT p.id, p.name, p.price, p.stock, c.name
        FROM products p
        JOIN categories c ON c.id = p.category_id
    """
    params = []
    if category_id is not None:
        sql += " WHERE p.category_id = :1"
        params.append(category_id)
    sql += " ORDER BY p.name"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [
                {"id": r[0], "name": r[1], "price": r[2], "stock": r[3], "category": r[4]}
                for r in cur.fetchall()
            ]

def get_product(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.name, p.description, p.price, p.stock, c.id, c.name
                FROM products p
                JOIN categories c ON c.id = p.category_id
                WHERE p.id = :1
                """,
                [product_id],
            )
            row = cur.fetchone()
            if row is None:
                return None

            product = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": row[3],
                "stock": row[4],
                "category_id": row[5],
                "category": row[6],
            }

            cur.execute(
                "SELECT attr_name, attr_value FROM product_attributes "
                "WHERE product_id = :1 ORDER BY id",
                [product_id],
            )
            product["attributes"] = [
                {"name": r[0], "value": r[1]} for r in cur.fetchall()
            ]
            return product

def get_products_by_ids(ids):
    """Връща {id: продукт} за няколко продукта с една заявка."""
    ids = list(ids)
    if not ids:
        return {}

    placeholders = ", ".join(f":{i + 1}" for i in range(len(ids)))
    sql = f"SELECT id, name, price, stock FROM products WHERE id IN ({placeholders})"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, ids)
            return {
                r[0]: {"id": r[0], "name": r[1], "price": r[2], "stock": r[3]}
                for r in cur.fetchall()
            }

def create_user(email, password_hash, name, phone):
    """Връща id на новия потребител или None, ако имейлът вече е зает."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            new_id = cur.var(int)
            try:
                cur.execute(
                    "INSERT INTO users (email, password_hash, name, phone) "
                    "VALUES (:1, :2, :3, :4) RETURNING id INTO :5",
                    [email, password_hash, name, phone, new_id],
                )
            except oracledb.IntegrityError:
                return None
        conn.commit()
        return new_id.getvalue()[0]


def get_user_by_email(email):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, password_hash FROM users WHERE email = :1",
                [email],
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "name": row[2], "password_hash": row[3]}

class OrderError(Exception):
    """Грешка, която може да се покаже на клиента."""


def create_order(user_id, contact_name, contact_email, token,
                 cart, address, phone, part_request=None):
    """user_id може да е None (поръчка без акаунт).
    cart е {product_id: quantity}. Записва всичко или нищо."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            lines = []
            total = Decimal("0")

            for product_id in sorted(cart):
                quantity = cart[product_id]
                cur.execute(
                    "SELECT name, price, stock FROM products "
                    "WHERE id = :1 FOR UPDATE",
                    [product_id],
                )
                row = cur.fetchone()
                if row is None:
                    raise OrderError("Продукт от количката вече не се продава.")
                name, price, stock = row
                if quantity > stock:
                    raise OrderError(
                        f"Няма достатъчно наличност за „{name}“ (налични: {stock})."
                    )
                price = Decimal(str(price))
                total += price * quantity
                lines.append((product_id, quantity, price))

            order_id_var = cur.var(int)
            cur.execute(
                "INSERT INTO orders (user_id, contact_name, contact_email, "
                "public_token, total, address, phone) "
                "VALUES (:1, :2, :3, :4, :5, :6, :7) RETURNING id INTO :8",
                [user_id, contact_name, contact_email, token,
                 total, address, phone, order_id_var],
            )
            order_id = order_id_var.getvalue()[0]

            for product_id, quantity, price in lines:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                    "VALUES (:1, :2, :3, :4)",
                    [order_id, product_id, quantity, price],
                )
                cur.execute(
                    "UPDATE products SET stock = stock - :1 WHERE id = :2",
                    [quantity, product_id],
                )

            if part_request:
                cur.execute(
                    "INSERT INTO part_requests (order_id, user_id, contact_name, "
                    "contact_email, contact_phone, car_make, car_model, car_year, "
                    "vin, description) "
                    "VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)",
                    [
                        order_id, user_id, contact_name, contact_email, phone,
                        part_request["make"], part_request["model"],
                        part_request["year"], part_request["vin"],
                        part_request["description"],
                    ],
                )

        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_order_by_token(token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, created_at, status, total, address, phone, contact_name "
                "FROM orders WHERE public_token = :1",
                [token],
            )
            row = cur.fetchone()
            if row is None:
                return None
            order = {
                "id": row[0], "created_at": row[1], "status": row[2],
                "total": row[3], "address": row[4], "phone": row[5],
                "contact_name": row[6],
            }

            cur.execute(
                "SELECT p.name, oi.quantity, oi.unit_price "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "WHERE oi.order_id = :1 ORDER BY oi.id",
                [order["id"]],
            )
            order["items"] = [
                {"name": r[0], "quantity": r[1], "unit_price": r[2]}
                for r in cur.fetchall()
            ]

            cur.execute(
                "SELECT car_make, car_model, car_year, description "
                "FROM part_requests WHERE order_id = :1 ORDER BY id",
                [order["id"]],
            )
            order["part_requests"] = [
                {"make": r[0], "model": r[1], "year": r[2], "description": r[3]}
                for r in cur.fetchall()
            ]
            return order