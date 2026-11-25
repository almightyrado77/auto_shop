from db import get_connection


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