from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # allow frontend requests

# -----------------------
# Database configuration
# -----------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///supermarket.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# -----------------------
# Models
# -----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    product = db.relationship('Product')

# Ensure database exists
with app.app_context():
    db.create_all()

# -----------------------
# Serve static files
# -----------------------
@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "File not found", 404

# -----------------------
# Home / Dashboard pages
# -----------------------
@app.route("/")
def home():
    try:
        return render_template("index.html")
    except:
        return open("index.html").read()

@app.route("/dashboard")
def dashboard():
    try:
        return render_template("dashboard.html")
    except:
        return open("dashboard.html").read()

# -----------------------
# API Endpoints
# -----------------------

# Register
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        fullname = data.get("fullname")
        username = data.get("username")
        password = data.get("password")

        if not fullname or not username or not password:
            return jsonify({"error": "Missing fields"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(fullname=fullname, username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print("Register Error:", e)
        return jsonify({"error": "Server error"}), 500

# Login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return jsonify({
                "id": user.id,
                "fullname": user.fullname,
                "username": user.username,
                "message": "Login successful"
            }), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"error": "Server error"}), 500

# Get all users (for debug)
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "fullname": u.fullname, "username": u.username} for u in users])

# Products
@app.route('/api/products', methods=['GET', 'POST'])
def products_api():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify([{"id": p.id, "name": p.name, "stock": p.stock, "price": p.price} for p in products])
    
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        stock = int(data.get('stock', 0))
        price = float(data.get('price', 0))
        if not name:
            return jsonify({"error":"Product name required"}), 400
        p = Product(name=name, stock=stock, price=price)
        db.session.add(p)
        db.session.commit()
        return jsonify({"message":"Product added successfully"}), 201

# Sales
@app.route('/api/sales', methods=['GET', 'POST'])
def sales_api():
    if request.method == 'GET':
        sales = Sale.query.all()
        return jsonify([
            {
                "id": s.id,
                "product": s.product.name,
                "qty": s.quantity,
                "amount": s.amount,
                "date": s.date
            } for s in sales
        ])

    if request.method == 'POST':
        data = request.get_json()
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity',0))
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error":"Product not found"}), 404
        if quantity > product.stock:
            return jsonify({"error":"Insufficient stock"}), 400
        amount = quantity * product.price
        product.stock -= quantity
        sale = Sale(product_id=product_id, quantity=quantity, amount=amount, date=datetime.today().strftime("%Y-%m-%d"))
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message":"Sale added successfully"}), 201

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
