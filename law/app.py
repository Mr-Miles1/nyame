from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# -----------------------
# Database configuration
# -----------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nyame.db'
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
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    product = db.relationship("Product")

# Create database tables
with app.app_context():
    db.create_all()

# -----------------------
# Routes
# -----------------------
@app.route('/')
def home():
    return send_file("index.html")

@app.route('/dashboard')
def dashboard():
    return send_file("dashboard.html")

@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "File not found", 404

# -----------------------
# API Endpoints
# -----------------------

# Register
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
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
        data = request.json
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return jsonify({
                "fullname": user.fullname,
                "username": user.username,
                "message": "Login successful"
            }), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"error": "Server error"}), 500

# Products CRUD
@app.route('/api/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify([{"id":p.id,"name":p.name,"stock":p.stock,"price":p.price} for p in products])
    if request.method == 'POST':
        data = request.json
        p = Product(name=data['name'], stock=data['stock'], price=data['price'])
        db.session.add(p)
        db.session.commit()
        return jsonify({"message":"Product added"}), 201

@app.route('/api/products/<int:id>', methods=['PUT', 'DELETE'])
def update_product(id):
    p = Product.query.get_or_404(id)
    data = request.json
    if request.method == 'PUT':
        p.name = data['name']
        p.stock = data['stock']
        p.price = data['price']
        db.session.commit()
        return jsonify({"message":"Product updated"})
    if request.method == 'DELETE':
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message":"Product deleted"})

# Sales CRUD
@app.route('/api/sales', methods=['GET', 'POST'])
def sales():
    if request.method == 'GET':
        sales = Sale.query.all()
        return jsonify([{
            "id":s.id,
            "date":s.date,
            "product":s.product.name,
            "qty":s.qty,
            "amount":s.amount
        } for s in sales])
    if request.method == 'POST':
        data = request.json
        product = Product.query.get_or_404(data['product_id'])
        if product.stock < data['qty']:
            return jsonify({"error":"Insufficient stock"}), 400
        product.stock -= data['qty']
        sale = Sale(date=datetime.now().strftime("%Y-%m-%d"), product_id=product.id,
                    qty=data['qty'], amount=data['qty']*product.price)
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message":"Sale added"}), 201

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sale.query.get_or_404(id)
    sale.product.stock += sale.qty  # restore stock
    db.session.delete(sale)
    db.session.commit()
    return jsonify({"message":"Sale deleted"})

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    if not os.path.exists("nyame.db"):
        open("nyame.db","a").close()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
