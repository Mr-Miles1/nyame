from flask import Flask, send_from_directory, request, jsonify
app = Flask(__name__, static_folder=".")

# Serve login page
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# Serve dashboard page
@app.route("/dashboard")
def dashboard():
    return send_from_directory(".", "dashboard.html")

# Example: static files (like logo.png)
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# ---------------- API endpoints ----------------
products = []
sales = []
product_id_counter = 1
sale_id_counter = 1

@app.route("/api/products", methods=["GET","POST"])
def api_products():
    global products, product_id_counter
    if request.method=="GET":
        return jsonify(products)
    data = request.json
    new_product = {"id": product_id_counter, "name":data["name"], "stock":data["stock"], "price":data["price"]}
    product_id_counter += 1
    products.append(new_product)
    return jsonify(new_product)

@app.route("/api/products/<int:pid>", methods=["PUT","DELETE"])
def api_product(pid):
    global products
    product = next((p for p in products if p["id"]==pid), None)
    if not product:
        return jsonify({"error":"Not found"}), 404
    if request.method=="PUT":
        data = request.json
        product.update({"name":data["name"], "stock":data["stock"], "price":data["price"]})
        return jsonify(product)
    if request.method=="DELETE":
        products = [p for p in products if p["id"]!=pid]
        return jsonify({"success":True})

@app.route("/api/sales", methods=["GET","POST"])
def api_sales():
    global sales, sale_id_counter, products
    if request.method=="GET":
        result = [{"id":s["id"], "date":s["date"], "product":next(p["name"] for p in products if p["id"]==s["product_id"]), "qty":s["qty"], "amount":s["amount"]} for s in sales]
        return jsonify(result)
    data = request.json
    product = next((p for p in products if p["id"]==data["product_id"]), None)
    if not product: return jsonify({"error":"Product not found"}), 404
    if data["qty"]>product["stock"]: return jsonify({"error":"Insufficient stock"}), 400
    product["stock"] -= data["qty"]
    new_sale = {"id": sale_id_counter, "product_id":data["product_id"], "qty":data["qty"], "amount":product["price"]*data["qty"], "date":data.get("date") or __import__("datetime").date.today().isoformat()}
    sale_id_counter += 1
    sales.append(new_sale)
    return jsonify(new_sale)

@app.route("/api/sales/<int:sid>", methods=["DELETE"])
def api_sale(sid):
    global sales
    sales = [s for s in sales if s["id"]!=sid]
    return jsonify({"success":True})

if __name__=="__main__":
    app.run(debug=True)
