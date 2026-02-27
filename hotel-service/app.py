from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["hotel_db"]
hotels_collection = db["hotels"]


def serialize(hotel):
    """Convert MongoDB document to JSON-serializable dict."""
    hotel["_id"] = str(hotel["_id"])
    return hotel


# ─────────────────────────────────────────
# GET /hotels — list all hotels
# ─────────────────────────────────────────
@app.route("/hotels", methods=["GET"])
def get_hotels():
    hotels = list(hotels_collection.find())
    return jsonify([serialize(h) for h in hotels]), 200


# ─────────────────────────────────────────
# GET /hotels/<id> — get one hotel
# ─────────────────────────────────────────
@app.route("/hotels/<hotel_id>", methods=["GET"])
def get_hotel(hotel_id):
    try:
        hotel = hotels_collection.find_one({"_id": ObjectId(hotel_id)})
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400

    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404

    return jsonify(serialize(hotel)), 200


# ─────────────────────────────────────────
# POST /hotels — create a hotel
# ─────────────────────────────────────────
@app.route("/hotels", methods=["POST"])
def create_hotel():
    data = request.json

    required_fields = ["name", "location", "star_rating"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_hotel = {
        "name":         data["name"],
        "location":     data["location"],
        "star_rating":  data["star_rating"],
        "amenities":    data.get("amenities", []),
        "description":  data.get("description", ""),
        "phone":        data.get("phone", ""),
        "email":        data.get("email", ""),
    }

    result = hotels_collection.insert_one(new_hotel)
    new_hotel["_id"] = str(result.inserted_id)

    return jsonify(new_hotel), 201


# ─────────────────────────────────────────
# PUT /hotels/<id> — update a hotel
# ─────────────────────────────────────────
@app.route("/hotels/<hotel_id>", methods=["PUT"])
def update_hotel(hotel_id):
    try:
        hotel = hotels_collection.find_one({"_id": ObjectId(hotel_id)})
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400

    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404

    data = request.json
    hotels_collection.update_one(
        {"_id": ObjectId(hotel_id)},
        {"$set": data}
    )

    updated = hotels_collection.find_one({"_id": ObjectId(hotel_id)})
    return jsonify(serialize(updated)), 200


# ─────────────────────────────────────────
# DELETE /hotels/<id> — delete a hotel
# ─────────────────────────────────────────
@app.route("/hotels/<hotel_id>", methods=["DELETE"])
def delete_hotel(hotel_id):
    try:
        result = hotels_collection.delete_one({"_id": ObjectId(hotel_id)})
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Hotel not found"}), 404

    return jsonify({"message": "Hotel deleted"}), 200


# ─────────────────────────────────────────
# Health check
# ─────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "hotel-service"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)