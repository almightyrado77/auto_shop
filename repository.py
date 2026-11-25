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