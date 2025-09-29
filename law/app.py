import os
import traceback
from datetime import date
from flask import Flask, send_from_directory, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)  # we will serve files manually from BASE_DIR
CORS(app)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'supermarket.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ---------------- Models ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    def to_dict(self):
        return {"id": self.id, "fullname": self.fullname, "username": self.username}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    def to_dict(self):
        return {"id": self.id, "name": self.name, "stock": self.stock, "price": self.price}

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    product = db.relationship('Product')
    def to_dict(self):
        return {"id": self.id, "product": self.product.name if self.product else None,
                "product_id": self.product_id, "qty": self.quantity, "amount": self.amount, "date": self.date}

# ensure DB exists
with app.app_context():
    db.create_all()

# ---------------- Serve UI files ----------------
def send_file_if_exists(filename):
    path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(path):
        return send_from_directory(BASE_DIR, filename)
    abort(404)

@app.route("/", methods=["GET"])
def route_index():
    return send_file_if_exists("index.html")

@app.route("/dashboard", methods=["GET"])
def route_dashboard():
    return send_file_if_exists("dashboard.html")

# serve other static files (logo.png etc). Put this AFTER API routes (see below) to avoid interfering.
# We'll attach it at bottom so API routes are matched first.

# ---------------- API: Users ----------------
@app.route("/api/register", methods=["POST"])
def api_register():
    try:
        data = request.get_json(force=True)
        fullname = (data or {}).get("fullname")
        username = (data or {}).get("username")
        password = (data or {}).get("password")
        if not fullname or not username or not password:
            return jsonify({"error": "Missing fields"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        u = User(fullname=fullname, username=username, password=hashed_pw)
        db.session.add(u)
        db.session.commit()
        return jsonify({"message": "User registered", "user": u.to_dict()}), 201
    except Exception as e:
        print("REGISTER ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json(force=True)
        username = (data or {}).get("username")
        password = (data or {}).get("password")
        if not username or not password:
            return jsonify({"error": "Missing credentials"}), 400
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return jsonify({"message": "Login successful", "id": user.id, "fullname": user.fullname, "username": user.username}), 200
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        print("LOGIN ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

@app.route("/api/user", methods=["GET"])
def api_user():
    # Minimal: return empty object if no username header/query provided.
    # If client sends ?username=... this will return that user's info.
    try:
        q = request.args.get("username")
        if q:
            u = User.query.filter_by(username=q).first()
            return jsonify(u.to_dict() if u else {}), 200
        return jsonify({}), 200
    except Exception as e:
        print("API_USER ERROR:\n", traceback.format_exc())
        return jsonify({}), 200

# ---------------- API: Products ----------------
@app.route("/api/products", methods=["GET", "POST"])
def api_products():
    try:
        if request.method == "GET":
            products = Product.query.all()
            return jsonify([p.to_dict() for p in products]), 200
        data = request.get_json(force=True)
        name = (data or {}).get("name")
        stock = int((data or {}).get("stock", 0))
        price = float((data or {}).get("price", 0.0))
        if not name:
            return jsonify({"error": "Missing product name"}), 400
        p = Product(name=name, stock=stock, price=price)
        db.session.add(p)
        db.session.commit()
        return jsonify({"message": "Product added", "product": p.to_dict()}), 201
    except Exception as e:
        print("PRODUCTS ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

@app.route("/api/products/<int:pid>", methods=["PUT", "DELETE"])
def api_product_modify(pid):
    try:
        p = Product.query.get(pid)
        if not p:
            return jsonify({"error": "Not found"}), 404
        if request.method == "DELETE":
            db.session.delete(p)
            db.session.commit()
            return jsonify({"message": "Deleted"}), 200
        data = request.get_json(force=True)
        p.name = (data or {}).get("name", p.name)
        p.stock = int((data or {}).get("stock", p.stock))
        p.price = float((data or {}).get("price", p.price))
        db.session.commit()
        return jsonify({"message": "Updated", "product": p.to_dict()}), 200
    except Exception as e:
        print("PRODUCT MODIFY ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

# ---------------- API: Sales ----------------
@app.route("/api/sales", methods=["GET", "POST"])
def api_sales():
    try:
        if request.method == "GET":
            sales = Sale.query.order_by(Sale.id.asc()).all()
            return jsonify([s.to_dict() for s in sales]), 200
        data = request.get_json(force=True)
        product_id = int((data or {}).get("product_id", 0))
        qty = int((data or {}).get("qty", 0))
        if not product_id or qty <= 0:
            return jsonify({"error": "Missing product_id or qty"}), 400
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        if qty > product.stock:
            return jsonify({"error": "Insufficient stock"}), 400
        product.stock -= qty
        sale = Sale(product_id=product_id, quantity=qty, amount=qty * product.price, date=date.today().isoformat())
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message": "Sale recorded", "sale": sale.to_dict()}), 201
    except Exception as e:
        print("SALES ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

@app.route("/api/sales/<int:sid>", methods=["DELETE"])
def api_sale_delete(sid):
    try:
        s = Sale.query.get(sid)
        if not s:
            return jsonify({"error": "Not found"}), 404
        # restore stock
        if s.product:
            s.product.stock += s.quantity
        db.session.delete(s)
        db.session.commit()
        return jsonify({"message": "Deleted"}), 200
    except Exception as e:
        print("SALE DELETE ERROR:\n", traceback.format_exc())
        return jsonify({"error": "Server error"}), 500

# ---------------- Serve static files (last) ----------------
@app.route("/<path:filename>", methods=["GET"])
def route_static_files(filename):
    # don't allow escaping base dir
    safe_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(safe_path):
        return send_from_directory(BASE_DIR, filename)
    return abort(404)

# ---------------- Run ----------------
if __name__ == "__main__":
    # create DB file if missing
    sqlite_path = os.path.join(BASE_DIR, "supermarket.db")
    if not os.path.exists(sqlite_path):
        open(sqlite_path, "a").close()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
