# booking-service

The core service of the Hotel Booking App. Handles all bookings and links **hotel-service**, **room-service**, and **user-service** together.

Runs on port **5003**.

## Dependencies

- **room-service** (port 5001) — validates room exists and marks it unavailable on booking
- **user-service** (port 5002) — validates user exists before booking

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookings` | Create a new booking |
| GET | `/bookings` | List all bookings (filter by `?user_id=` and `?status=`) |
| GET | `/bookings/<booking_id>` | Get one booking |
| PATCH | `/bookings/<booking_id>/cancel` | Cancel a booking |
| DELETE | `/bookings/<booking_id>` | Delete a booking |
| GET | `/health` | Health check |

## Booking Schema

```json
{
  "user_id": "string (required)",
  "room_id": "string (required)",
  "check_in": "string (required, YYYY-MM-DD)",
  "check_out": "string (required, YYYY-MM-DD)",
  "hotel_id": "string (auto-filled from room)",
  "nights": "number (auto-calculated)",
  "total_price": "number (auto-calculated)",
  "status": "string (confirmed or cancelled)",
  "created_at": "string (ISO timestamp)"
}
```

## Example Requests

**Create a booking**
```bash
curl -X POST http://localhost:5003/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "room_id": "<room_id>",
    "check_in": "2026-04-01",
    "check_out": "2026-04-05"
  }'
```

**Get bookings for a user**
```bash
curl http://localhost:5003/bookings?user_id=<user_id>
```

**Cancel a booking**
```bash
curl -X PATCH http://localhost:5003/bookings/<booking_id>/cancel
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
MONGO_URI=mongodb://localhost:27017 python app.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `ROOM_SERVICE_URL` | `http://localhost:5001` | Room service base URL |
| `USER_SERVICE_URL` | `http://localhost:5002` | User service base URL |