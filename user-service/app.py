from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import hashlib

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["hotel_booking"]
users_collection = db["users"]


def serialize(user):
    """Convert MongoDB document to JSON-serializable dict."""
    user["_id"] = str(user["_id"])
    return user


def hash_password(password):
    """Simple SHA-256 password hash."""
    return hashlib.sha256(password.encode()).hexdigest()


# ── CREATE ────────────────────────────────────────────────────────────────────

# POST /users - register a new user
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Check for duplicate email
    existing = users_collection.find_one({"email": data["email"]})
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    new_user = {
        "name": data["name"],
        "email": data["email"],
        "password": hash_password(data["password"]),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
        "role": data.get("role", "guest"),  # guest or admin
    }

    result = users_collection.insert_one(new_user)
    new_user = users_collection.find_one({"_id": result.inserted_id})
    new_user.pop("password")  # never return password
    return jsonify(serialize(new_user)), 201


# ── READ ──────────────────────────────────────────────────────────────────────

# GET /users - list all users
@app.route("/users", methods=["GET"])
def get_users():
    users = list(users_collection.find())
    for user in users:
        user.pop("password")  # never return password
    return jsonify([serialize(u) for u in users]), 200


# GET /users/<user_id> - get one user
@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400

    if not user:
        return jsonify({"error": "User not found"}), 404

    user.pop("password")
    return jsonify(serialize(user)), 200


# ── UPDATE ────────────────────────────────────────────────────────────────────

# PUT /users/<user_id> - update a user
@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        object_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400

    data = request.get_json()

    # Prevent overwriting _id
    data.pop("_id", None)

    # Hash password if being updated
    if "password" in data:
        data["password"] = hash_password(data["password"])

    result = users_collection.update_one({"_id": object_id}, {"$set": data})

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    updated_user = users_collection.find_one({"_id": object_id})
    updated_user.pop("password")
    return jsonify(serialize(updated_user)), 200


# ── DELETE ────────────────────────────────────────────────────────────────────

# DELETE /users/<user_id> - delete a user
@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        object_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID format"}), 400

    result = users_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted successfully"}), 200


# ── AUTH ──────────────────────────────────────────────────────────────────────

# POST /users/login - login
@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json()

    if "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    user = users_collection.find_one({
        "email": data["email"],
        "password": hash_password(data["password"])
    })

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    user.pop("password")
    return jsonify(serialize(user)), 200


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "user-service"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)