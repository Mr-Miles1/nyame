from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///supermarket.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ---------------- Models ----------------
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

with app.app_context():
    db.create_all()

# ---------------- User APIs ----------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data.get("fullname")
    username = data.get("username")
    password = data.get("password")
    if not fullname or not username or not password:
        return jsonify({"error": "Missing fields"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username exists"}), 400
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(fullname=fullname, username=username, password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message":"User registered"}),201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({"id":user.id,"fullname":user.fullname,"username":user.username,"message":"Login success"}),200
    return jsonify({"error":"Invalid credentials"}),401

# ---------------- Product APIs ----------------
@app.route('/api/products', methods=['GET','POST'])
def products_api():
    if request.method=='GET':
        products = Product.query.all()
        return jsonify([{"id":p.id,"name":p.name,"stock":p.stock,"price":p.price} for p in products])
    data = request.get_json()
    name = data.get('name')
    stock = int(data.get('stock',0))
    price = float(data.get('price',0))
    product = Product(name=name, stock=stock, price=price)
    db.session.add(product)
    db.session.commit()
    return jsonify({"message":"Product added"}),201

@app.route('/api/products/<int:id>', methods=['PUT','DELETE'])
def product_modify(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"error":"Not found"}),404
    if request.method=='DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message":"Deleted"})
    # PUT
    data = request.get_json()
    product.name = data.get('name',product.name)
    product.stock = data.get('stock',product.stock)
    product.price = data.get('price',product.price)
    db.session.commit()
    return jsonify({"message":"Updated"})

# ---------------- Sales APIs ----------------
@app.route('/api/sales', methods=['GET','POST'])
def sales_api():
    if request.method=='GET':
        sales = Sale.query.all()
        return jsonify([{"id":s.id,"product":s.product.name,"qty":s.quantity,"amount":s.amount,"date":s.date} for s in sales])
    data = request.get_json()
    product_id = int(data.get('product_id'))
    qty = int(data.get('qty',0))
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error":"Product not found"}),404
    if qty > product.stock:
        return jsonify({"error":"Insufficient stock"}),400
    product.stock -= qty
    sale = Sale(product_id=product_id, quantity=qty, amount=qty*product.price, date=datetime.today().strftime("%Y-%m-%d"))
    db.session.commit()
    db.session.add(sale)
    db.session.commit()
    return jsonify({"message":"Sale added"}),201

@app.route('/api/sales/<int:id>', methods=['DELETE'])
def sale_delete(id):
    sale = Sale.query.get(id)
    if not sale:
        return jsonify({"error":"Not found"}),404
    # restore stock
    sale.product.stock += sale.quantity
    db.session.delete(sale)
    db.session.commit()
    return jsonify({"message":"Deleted"})

# ---------------- Run ----------------
if __name__=="__main__":
    app.run(debug=True)
