from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import requests
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["hotel_booking"]
bookings_collection = db["bookings"]

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5002")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://localhost:5001")


def serialize(booking):
    """Convert MongoDB document to JSON-serializable dict."""
    booking["_id"] = str(booking["_id"])
    return booking


# ── CREATE ────────────────────────────────────────────────────────────────────

# POST /bookings - create a new booking
@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()

    required_fields = ["user_id", "room_id", "check_in", "check_out"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate user exists
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{data['user_id']}")
        if user_response.status_code != 200:
            return jsonify({"error": "User not found"}), 404
    except Exception:
        return jsonify({"error": "User service unavailable"}), 503

    # Validate room exists and is available
    try:
        room_response = requests.get(f"{ROOM_SERVICE_URL}/rooms/{data['room_id']}")
        if room_response.status_code != 200:
            return jsonify({"error": "Room not found"}), 404
        room = room_response.json()
        if not room.get("is_available"):
            return jsonify({"error": "Room is not available"}), 409
    except Exception:
        return jsonify({"error": "Room service unavailable"}), 503

    # Parse dates
    try:
        check_in = datetime.strptime(data["check_in"], "%Y-%m-%d")
        check_out = datetime.strptime(data["check_out"], "%Y-%m-%d")
        if check_out <= check_in:
            return jsonify({"error": "check_out must be after check_in"}), 400
    except ValueError:
        return jsonify({"error": "Date format must be YYYY-MM-DD"}), 400

    # Calculate total price
    nights = (check_out - check_in).days
    total_price = nights * room["price_per_night"]

    new_booking = {
        "user_id": data["user_id"],
        "room_id": data["room_id"],
        "hotel_id": room.get("hotel_id"),
        "check_in": data["check_in"],
        "check_out": data["check_out"],
        "nights": nights,
        "total_price": total_price,
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat(),
    }

    result = bookings_collection.insert_one(new_booking)

    # Mark room as unavailable
    try:
        requests.patch(
            f"{ROOM_SERVICE_URL}/rooms/{data['room_id']}/availability",
            json={"is_available": False}
        )
    except Exception:
        pass  # booking is already created, log this in production

    new_booking = bookings_collection.find_one({"_id": result.inserted_id})
    return jsonify(serialize(new_booking)), 201


# ── READ ──────────────────────────────────────────────────────────────────────

# GET /bookings - list all bookings
@app.route("/bookings", methods=["GET"])
def get_bookings():
    bookings = list(bookings_collection.find())
    return jsonify([serialize(b) for b in bookings]), 200


# GET /bookings/<booking_id> - get one booking
@app.route("/bookings/<booking_id>", methods=["GET"])
def get_booking(booking_id):
    try:
        booking = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        return jsonify({"error": "Invalid booking ID format"}), 400

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify(serialize(booking)), 200


# GET /bookings/user/<user_id> - get all bookings for a user
@app.route("/bookings/user/<user_id>", methods=["GET"])
def get_bookings_by_user(user_id):
    bookings = list(bookings_collection.find({"user_id": user_id}))
    return jsonify([serialize(b) for b in bookings]), 200


# GET /bookings/room/<room_id> - get all bookings for a room
@app.route("/bookings/room/<room_id>", methods=["GET"])
def get_bookings_by_room(room_id):
    bookings = list(bookings_collection.find({"room_id": room_id}))
    return jsonify([serialize(b) for b in bookings]), 200


# ── UPDATE ────────────────────────────────────────────────────────────────────

# PATCH /bookings/<booking_id>/cancel - cancel a booking
@app.route("/bookings/<booking_id>/cancel", methods=["PATCH"])
def cancel_booking(booking_id):
    try:
        object_id = ObjectId(booking_id)
    except Exception:
        return jsonify({"error": "Invalid booking ID format"}), 400

    booking = bookings_collection.find_one({"_id": object_id})
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking["status"] == "cancelled":
        return jsonify({"error": "Booking already cancelled"}), 400

    bookings_collection.update_one(
        {"_id": object_id},
        {"$set": {"status": "cancelled"}}
    )

    # Mark room as available again
    try:
        requests.patch(
            f"{ROOM_SERVICE_URL}/rooms/{booking['room_id']}/availability",
            json={"is_available": True}
        )
    except Exception:
        pass

    updated_booking = bookings_collection.find_one({"_id": object_id})
    return jsonify(serialize(updated_booking)), 200


# ── DELETE ────────────────────────────────────────────────────────────────────

# DELETE /bookings/<booking_id> - delete a booking
@app.route("/bookings/<booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    try:
        object_id = ObjectId(booking_id)
    except Exception:
        return jsonify({"error": "Invalid booking ID format"}), 400

    result = bookings_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({"message": "Booking deleted successfully"}), 200


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "booking-service"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)