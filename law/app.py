from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import datetime

app = Flask(__name__, static_folder=".")
CORS(app)

# ---------------- Web Routes ----------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory(".", "dashboard.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# ---------------- API Routes ----------------
products = []
sales = []
product_id_counter = 1
sale_id_counter = 1

@app.route("/api/products", methods=["GET", "POST"])
def api_products():
    global products, product_id_counter
    if request.method == "GET":
        return jsonify(products)

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    new_product = {
        "id": product_id_counter,
        "name": data.get("name"),
        "stock": data.get("stock"),
        "price": data.get("price")
    }

    if not new_product["name"] or new_product["stock"] is None or new_product["price"] is None:
        return jsonify({"error": "Missing product fields"}), 400

    product_id_counter += 1
    products.append(new_product)
    return jsonify(new_product), 201

@app.route("/api/products/<int:pid>", methods=["PUT", "DELETE"])
def api_product(pid):
    global products
    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        return jsonify({"error": "Not found"}), 404

    if request.method == "PUT":
        data = request.get_json()
        product.update({
            "name": data.get("name", product["name"]),
            "stock": data.get("stock", product["stock"]),
            "price": data.get("price", product["price"])
        })
        return jsonify(product)

    if request.method == "DELETE":
        products = [p for p in products if p["id"] != pid]
        return jsonify({"success": True})

@app.route("/api/sales", methods=["GET", "POST"])
def api_sales():
    global sales, sale_id_counter, products
    if request.method == "GET":
        result = [
            {
                "id": s["id"],
                "date": s["date"],
                "product": next((p["name"] for p in products if p["id"] == s["product_id"]), "Unknown"),
                "qty": s["qty"],
                "amount": s["amount"]
            }
            for s in sales
        ]
        return jsonify(result)

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    product = next((p for p in products if p["id"] == data.get("product_id")), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if data.get("qty", 0) > product["stock"]:
        return jsonify({"error": "Insufficient stock"}), 400

    product["stock"] -= data["qty"]
    new_sale = {
        "id": sale_id_counter,
        "product_id": data["product_id"],
        "qty": data["qty"],
        "amount": product["price"] * data["qty"],
        "date": data.get("date") or datetime.date.today().isoformat()
    }
    sale_id_counter += 1
    sales.append(new_sale)
    return jsonify(new_sale), 201

@app.route("/api/sales/<int:sid>", methods=["DELETE"])
def api_sale(sid):
    global sales
    sales = [s for s in sales if s["id"] != sid]
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
