from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import uuid
import random
import requests
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["hotel_booking"]
payments_collection = db["payments"]

# Service URLs
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://localhost:5003")


def serialize(payment):
    """Convert MongoDB document to JSON-serializable dict."""
    payment["_id"] = str(payment["_id"])
    return payment


def mock_charge(amount):
    """
    Simulate a payment gateway (e.g. Stripe).
    90% success rate to mimic real-world behavior.
    """
    success = random.random() < 0.9
    if success:
        return {
            "success": True,
            "transaction_id": f"mock_txn_{uuid.uuid4().hex[:12]}",
            "message": "Payment processed successfully"
        }
    return {
        "success": False,
        "transaction_id": None,
        "message": "Mock payment declined - insufficient funds"
    }


def mock_refund(transaction_id):
    """Simulate a refund. Always succeeds for mock purposes."""
    return {
        "success": True,
        "refund_id": f"mock_refund_{uuid.uuid4().hex[:12]}",
        "message": f"Refund issued for transaction {transaction_id}"
    }


# ── CREATE ────────────────────────────────────────────────────────────────────

# POST /payments - process a payment for a booking
@app.route("/payments", methods=["POST"])
def create_payment():
    data = request.get_json()

    required_fields = ["booking_id", "user_id", "amount"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if data["amount"] <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    # Validate booking exists
    try:
        booking_response = requests.get(f"{BOOKING_SERVICE_URL}/bookings/{data['booking_id']}")
        if booking_response.status_code != 200:
            return jsonify({"error": "Booking not found"}), 404
    except Exception:
        return jsonify({"error": "Booking service unavailable"}), 503

    # Check no successful payment already exists for this booking
    existing = payments_collection.find_one({
        "booking_id": data["booking_id"],
        "status": "success"
    })
    if existing:
        return jsonify({"error": "Booking already paid"}), 409

    # Call mock gateway
    result = mock_charge(data["amount"])
    status = "success" if result["success"] else "failed"

    new_payment = {
        "booking_id": data["booking_id"],
        "user_id": data["user_id"],
        "amount": data["amount"],
        "currency": data.get("currency", "USD"),
        "method": data.get("method", "mock_card"),
        "status": status,
        "transaction_id": result["transaction_id"],
        "created_at": datetime.utcnow().isoformat(),
    }

    inserted = payments_collection.insert_one(new_payment)
    new_payment = payments_collection.find_one({"_id": inserted.inserted_id})

    if not result["success"]:
        return jsonify({
            "error": result["message"],
            "payment": serialize(new_payment)
        }), 402

    return jsonify(serialize(new_payment)), 201


# ── READ ──────────────────────────────────────────────────────────────────────

# GET /payments - list all payments (payment history)
@app.route("/payments", methods=["GET"])
def get_payments():
    payments = list(payments_collection.find())
    return jsonify([serialize(p) for p in payments]), 200


# GET /payments/<payment_id> - get one payment / check status
@app.route("/payments/<payment_id>", methods=["GET"])
def get_payment(payment_id):
    try:
        payment = payments_collection.find_one({"_id": ObjectId(payment_id)})
    except Exception:
        return jsonify({"error": "Invalid payment ID format"}), 400

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify(serialize(payment)), 200


# GET /payments/booking/<booking_id> - get all payments for a booking
@app.route("/payments/booking/<booking_id>", methods=["GET"])
def get_payments_by_booking(booking_id):
    payments = list(payments_collection.find({"booking_id": booking_id}))
    return jsonify([serialize(p) for p in payments]), 200


# GET /payments/user/<user_id> - get payment history for a user
@app.route("/payments/user/<user_id>", methods=["GET"])
def get_payments_by_user(user_id):
    payments = list(payments_collection.find({"user_id": user_id}))
    return jsonify([serialize(p) for p in payments]), 200


# ── REFUND ────────────────────────────────────────────────────────────────────

# POST /payments/<payment_id>/refund - refund a payment
@app.route("/payments/<payment_id>/refund", methods=["POST"])
def refund_payment(payment_id):
    try:
        object_id = ObjectId(payment_id)
    except Exception:
        return jsonify({"error": "Invalid payment ID format"}), 400

    payment = payments_collection.find_one({"_id": object_id})
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    if payment["status"] != "success":
        return jsonify({"error": f"Cannot refund a payment with status: {payment['status']}"}), 400

    result = mock_refund(payment["transaction_id"])
    if not result["success"]:
        return jsonify({"error": "Refund failed at gateway"}), 500

    payments_collection.update_one(
        {"_id": object_id},
        {"$set": {"status": "refunded"}}
    )

    updated_payment = payments_collection.find_one({"_id": object_id})
    return jsonify(serialize(updated_payment)), 200


# ── DELETE ────────────────────────────────────────────────────────────────────

# DELETE /payments/<payment_id> - delete a payment record
@app.route("/payments/<payment_id>", methods=["DELETE"])
def delete_payment(payment_id):
    try:
        object_id = ObjectId(payment_id)
    except Exception:
        return jsonify({"error": "Invalid payment ID format"}), 400

    result = payments_collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify({"message": "Payment deleted successfully"}), 200


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "payment-service"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)