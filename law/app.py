from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# Serve login/register/forgot HTML
@app.route("/")
def home():
    return render_template("index.html")

# Register API
@app.route('/api/register', methods=['POST'])
def register():
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

# Login API
@app.route('/api/login', methods=['POST'])
def login():
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

# Dashboard page (simple placeholder)
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Debug route (optional)
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "fullname": u.fullname, "username": u.username} for u in users])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
