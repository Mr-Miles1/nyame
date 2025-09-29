from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # allow frontend requests

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
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

# Ensure database exists and tables are created
with app.app_context():
    db.create_all()

# -----------------------
# Routes
# -----------------------

# Serve static files (logo.png, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "File not found", 404

# Home / login page
@app.route("/")
def home():
    try:
        return render_template("index.html")
    except:
        return open("index.html").read()  # fallback if no templates folder

# Dashboard page
@app.route("/dashboard")
def dashboard():
    try:
        return render_template("dashboard.html")
    except:
        return open("dashboard.html").read()  # fallback if no templates folder

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

# Get all users (debug)
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "fullname": u.fullname, "username": u.username} for u in users])

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    # Ensure SQLite file is writable
    if not os.path.exists("users.db"):
        open("users.db", "a").close()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
