import os

from dotenv import load_dotenv
from flask import (Flask, abort, redirect, render_template, request,
                   session, url_for)

import repository
from cart import build_cart

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Липсва SECRET_KEY в .env")


@app.context_processor
def inject_cart_count():
    return {"cart_count": sum(session.get("cart", {}).values())}


@app.route("/")
def home():
    category_id = request.args.get("category", type=int)
    return render_template(
        "catalog.html",
        categories=repository.get_categories(),
        products=repository.get_products(category_id),
        selected=category_id,
    )


@app.route("/product/<int:product_id>")
def product_page(product_id):
    product = repository.get_product(product_id)
    if product is None:
        abort(404)
    return render_template("product.html", product=product)


@app.get("/cart")
def cart_page():
    cart = session.get("cart", {})
    products = repository.get_products_by_ids(int(k) for k in cart)
    items, total = build_cart(cart, products)
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/add/<int:product_id>")
def cart_add(product_id):
    product = repository.get_products_by_ids([product_id]).get(product_id)
    if product is None:
        abort(404)

    cart = session.get("cart", {})
    key = str(product_id)
    quantity = min(cart.get(key, 0) + 1, product["stock"])
    if quantity > 0:
        cart[key] = quantity
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.post("/cart/update/<int:product_id>")
def cart_update(product_id):
    quantity = request.form.get("quantity", type=int)
    cart = session.get("cart", {})
    key = str(product_id)

    if key in cart:
        product = repository.get_products_by_ids([product_id]).get(product_id)
        if quantity is None or quantity <= 0 or product is None:
            del cart[key]
        else:
            cart[key] = min(quantity, product["stock"])
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)