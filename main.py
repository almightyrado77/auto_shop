import secrets
from functools import wraps
import os

from dotenv import load_dotenv
from flask import (Flask, abort, redirect, render_template, request,
                   session, url_for)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

import repository
from cart import build_cart

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Липсва SECRET_KEY в .env")

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
csrf = CSRFProtect(app)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip() or None
        password = request.form.get("password", "")

        errors = []
        if not name or len(name) > 100:
            errors.append("Въведи име (до 100 символа).")
        if "@" not in email or len(email) > 255:
            errors.append("Въведи валиден имейл.")
        if phone and len(phone) > 30:
            errors.append("Телефонът е твърде дълъг.")
        if not 8 <= len(password) <= 128:
            errors.append("Паролата трябва да е между 8 и 128 символа.")

        if not errors:
            user_id = repository.create_user(
                email, generate_password_hash(password), name, phone
            )
            if user_id is None:
                errors.append("Вече има акаунт с този имейл.")
            else:
                session["user_id"] = user_id
                session["user_name"] = name
                session["user_email"] = email
                return redirect(url_for("home"))

        return render_template("register.html", errors=errors, form=request.form)

    return render_template("register.html", errors=[], form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = repository.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("home"))
        error = "Грешен имейл или парола."

    return render_template("login.html", error=error)


@app.post("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    return redirect(url_for("home"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("cart_page"))

    products = repository.get_products_by_ids(int(k) for k in cart)
    items, total = build_cart(cart, products)

    if request.method == "GET":
        return render_template(
            "checkout.html", items=items, total=total, errors=[], form={}
        )

    errors = []
    contact_name = request.form.get("contact_name", "").strip()
    contact_email = request.form.get("contact_email", "").strip().lower()
    address = request.form.get("address", "").strip()
    phone = request.form.get("phone", "").strip()

    if not 2 <= len(contact_name) <= 100:
        errors.append("Въведи име (2-100 символа).")
    if "@" not in contact_email or len(contact_email) > 255:
        errors.append("Въведи валиден имейл.")
    if not 5 <= len(address) <= 500:
        errors.append("Въведи адрес за доставка (5-500 символа).")
    if not 5 <= len(phone) <= 30:
        errors.append("Въведи телефон за връзка.")

    part_request = None
    if request.form.get("want_part"):
        make = request.form.get("car_make", "").strip()
        model = request.form.get("car_model", "").strip()
        year = request.form.get("car_year", type=int)
        vin = request.form.get("vin", "").strip().upper() or None
        description = request.form.get("part_description", "").strip()

        if not make or len(make) > 50:
            errors.append("Въведи марка на автомобила (до 50 символа).")
        if not model or len(model) > 50:
            errors.append("Въведи модел на автомобила (до 50 символа).")
        if year is not None and not 1950 <= year <= 2100:
            errors.append("Годината на автомобила не е валидна.")
        if vin and not (len(vin) == 17 and vin.isalnum()):
            errors.append("VIN номерът е с 17 букви и цифри.")
        if not 5 <= len(description) <= 2000:
            errors.append("Опиши търсената част (5-2000 символа).")

        part_request = {
            "make": make, "model": model, "year": year,
            "vin": vin, "description": description,
        }

    if not errors:
        token = secrets.token_urlsafe(32)
        try:
            repository.create_order(
                session.get("user_id"),
                contact_name,
                contact_email,
                token,
                {int(k): v for k, v in cart.items()},
                address,
                phone,
                part_request,
            )
        except repository.OrderError as e:
            errors.append(str(e))
        else:
            session.pop("cart", None)
            return redirect(url_for("order_done", token=token))

    return render_template(
        "checkout.html", items=items, total=total, errors=errors, form=request.form
    )


@app.get("/order/<token>")
def order_done(token):
    order = repository.get_order_by_token(token)
    if order is None:
        abort(404)
    return render_template("order.html", order=order)


if __name__ == "__main__":
    app.run(debug=True)