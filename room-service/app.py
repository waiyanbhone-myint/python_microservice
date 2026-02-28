from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["hotel_booking"]
rooms_collection = db["rooms"]


def serialize(room):
    """Convert MongoDB document to JSON-serializable dict."""
    room["_id"] = str(room["_id"])
    return room

# CREATE ────────────────────────────────────────────────────────────────────

# POST /rooms - create a new room
@app.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json()

    required_fields = ["hotel_id", "room_number", "room_type", "price_per_night", "capacity"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate hotel_id is a valid ObjectId
    try:
        data["hotel_id"] = str(ObjectId(data["hotel_id"]))
    except Exception:
        return jsonify({"error": "Invalid hotel_id format"}), 400

    # Check for duplicate room number in the same hotel
    existing = rooms_collection.find_one({
        "hotel_id": data["hotel_id"],
        "room_number": data["room_number"]
    })
    if existing:
        return jsonify({"error": "Room number already exists for this hotel"}), 409

    # Default is_available to True if not provided
    data.setdefault("is_available", True)
    data.setdefault("amenities", [])

    result = rooms_collection.insert_one(data)
    new_room = rooms_collection.find_one({"_id": result.inserted_id})
    return jsonify(serialize(new_room)), 201


# ── READ ──────────────────────────────────────────────────────────────────────

# GET /rooms - list all rooms (optional ?hotel_id=... and ?available=true/false)
@app.route("/rooms", methods=["GET"])
def get_rooms():
    query = {}

    hotel_id = request.args.get("hotel_id")
    if hotel_id:
        query["hotel_id"] = hotel_id

    available = request.args.get("available")
    if available is not None:
        query["is_available"] = available.lower() == "true"

    rooms = list(rooms_collection.find(query))
    return jsonify([serialize(r) for r in rooms]), 200


# GET /rooms/<room_id> - get one room by ID
@app.route("/rooms/<room_id>", methods=["GET"])
def get_room(room_id):
    try:
        room = rooms_collection.find_one({"_id": ObjectId(room_id)})
    except Exception:
        return jsonify({"error": "Invalid room ID format"}), 400

    if not room:
        return jsonify({"error": "Room not found"}), 404

    return jsonify(serialize(room)), 200


# GET /rooms/hotel/<hotel_id> - get all rooms for a specific hotel
@app.route("/rooms/hotel/<hotel_id>", methods=["GET"])
def get_rooms_by_hotel(hotel_id):
    rooms = list(rooms_collection.find({"hotel_id": hotel_id}))
    return jsonify([serialize(r) for r in rooms]), 200


# ── UPDATE ────────────────────────────────────────────────────────────────────

# PUT /rooms/<room_id> - update a room
@app.route("/rooms/<room_id>", methods=["PUT"])
def update_room(room_id):
    try:
        object_id = ObjectId(room_id)
    except Exception:
        return jsonify({"error": "Invalid room ID format"}), 400

    data = request.get_json()

    # Prevent overwriting _id
    data.pop("_id", None)

    result = rooms_collection.update_one({"_id": object_id}, {"$set": data})

    if result.matched_count == 0:
        return jsonify({"error": "Room not found"}), 404

    updated_room = rooms_collection.find_one({"_id": object_id})
    return jsonify(serialize(updated_room)), 200


# PATCH /rooms/<room_id>/availability - toggle room availability
@app.route("/rooms/<room_id>/availability", methods=["PATCH"])
def update_availability(room_id):
    try:
        object_id = ObjectId(room_id)
    except Exception:
        return jsonify({"error": "Invalid room ID format"}), 400

    data = request.get_json()
    if "is_available" not in data:
        return jsonify({"error": "Missing field: is_available"}), 400

    result = rooms_collection.update_one(
        {"_id": object_id},
        {"$set": {"is_available": data["is_available"]}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Room not found"}), 404

    updated_room = rooms_collection.find_one({"_id": object_id})
    return jsonify(serialize(updated_room)), 200


# ── DELETE ────────────────────────────────────────────────────────────────────

# DELETE /rooms/<room_id> - delete a room
@app.route("/rooms/<room_id>", methods=["DELETE"])
def delete_room(room_id):
    try:
        object_id = ObjectId(room_id)
    except Exception:
        return jsonify({"error": "Invalid room ID format"}), 400

    result = rooms_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Room not found"}), 404

    return jsonify({"message": "Room deleted successfully"}), 200


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "room-service"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)