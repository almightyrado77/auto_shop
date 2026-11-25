from flask import Flask, abort, render_template, request

import repository

app = Flask(__name__)


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


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)