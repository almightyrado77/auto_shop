from pathlib import Path

from db import get_connection

CATEGORIES = ["Масла", "Антифриз", "Крушки", "Акумулатори", "Аксесоари"]

# (категория, име, описание, цена в евро, наличност, характеристики)
PRODUCTS = [
    ("Масла", "Моторно масло 5W-30 5л",
     "Синтетично масло за съвременни бензинови и дизелови двигатели.", 42.90, 25,
     {"Вискозитет": "5W-30", "Обем": "5 л", "Тип": "Синтетично"}),
    ("Масла", "Моторно масло 10W-40 4л",
     "Полусинтетично масло за по-стари двигатели.", 29.90, 30,
     {"Вискозитет": "10W-40", "Обем": "4 л", "Тип": "Полусинтетично"}),
    ("Антифриз", "Антифриз G12 5л",
     "Антифриз за охладителната система, защита до -35°C.", 14.50, 40,
     {"Цвят": "Червен", "Обем": "5 л", "Защита": "-35°C"}),
    ("Крушки", "Крушка H7 12V 55W",
     "Халогенна крушка за къси и дълги светлини.", 4.50, 100,
     {"Тип": "H7", "Напрежение": "12 V", "Мощност": "55 W"}),
    ("Крушки", "Крушка H4 12V 60/55W",
     "Халогенна крушка с две нишки.", 4.90, 80,
     {"Тип": "H4", "Напрежение": "12 V", "Мощност": "60/55 W"}),
    ("Акумулатори", "Акумулатор 60Ah 540A",
     "Стартерен акумулатор за леки автомобили.", 89.00, 12,
     {"Капацитет": "60 Ah", "Стартов ток": "540 A", "Напрежение": "12 V"}),
    ("Акумулатори", "Акумулатор 74Ah 680A",
     "Стартерен акумулатор за по-големи двигатели.", 119.00, 8,
     {"Капацитет": "74 Ah", "Стартов ток": "680 A", "Напрежение": "12 V"}),
    ("Аксесоари", "Чистачки 600 мм",
     "Плоски чистачки за предното стъкло.", 12.00, 50,
     {"Дължина": "600 мм", "Вид": "Плоски"}),
    ("Аксесоари", "Кабели за палене 400A",
     "Кабели за подаване на ток към изтощен акумулатор.", 18.50, 20,
     {"Ток": "400 A", "Дължина": "3 м"}),
]


def run_schema(cur):
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    for statement in schema.split(";"):
        if statement.strip():
            cur.execute(statement)


def seed(cur):
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] > 0:
        print("Примерните данни вече са заредени.")
        return

    for name in CATEGORIES:
        cur.execute("INSERT INTO categories (name) VALUES (:1)", [name])

    for category, name, description, price, stock, attrs in PRODUCTS:
        cur.execute("SELECT id FROM categories WHERE name = :1", [category])
        category_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO products (category_id, name, description, price, stock) "
            "VALUES (:1, :2, :3, :4, :5)",
            [category_id, name, description, price, stock],
        )
        cur.execute("SELECT id FROM products WHERE name = :1", [name])
        product_id = cur.fetchone()[0]
        for attr_name, attr_value in attrs.items():
            cur.execute(
                "INSERT INTO product_attributes (product_id, attr_name, attr_value) "
                "VALUES (:1, :2, :3)",
                [product_id, attr_name, attr_value],
            )
    print(f"Заредени: {len(CATEGORIES)} категории, {len(PRODUCTS)} продукта.")


if __name__ == "__main__":
    with get_connection() as conn:
        with conn.cursor() as cur:
            run_schema(cur)
            seed(cur)
        conn.commit()
    print("Базата е готова.")