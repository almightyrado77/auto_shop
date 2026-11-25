from flask import Flask, render_template, request

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


if __name__ == "__main__":
    app.run(debug=True)