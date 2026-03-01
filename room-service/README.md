# room-service

Manages room data for the Hotel Booking App. Every room belongs to a hotel, so **hotel-service must be running** before using this service.

Runs on port **5001**.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rooms` | Create a new room |
| GET | `/rooms` | List all rooms (supports filters) |
| GET | `/rooms/<room_id>` | Get one room by ID |
| GET | `/rooms/hotel/<hotel_id>` | Get all rooms for a hotel |
| PUT | `/rooms/<room_id>` | Update a room |
| PATCH | `/rooms/<room_id>/availability` | Update room availability |
| DELETE | `/rooms/<room_id>` | Delete a room |
| GET | `/health` | Health check |

## Room Schema

```json
{
  "hotel_id": "string (required - ObjectId of the hotel)",
  "room_number": "string (required, e.g. '101')",
  "room_type": "string (required, e.g. 'single', 'double', 'suite')",
  "price_per_night": "number (required)",
  "capacity": "number (required)",
  "is_available": "boolean (default: true)",
  "amenities": ["wifi", "tv", "minibar"]
}
```

## Example Requests

**Create a room**
```bash
curl -X POST http://localhost:5001/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_id": "<hotel_id>",
    "room_number": "101",
    "room_type": "double",
    "price_per_night": 150,
    "capacity": 2
  }'
```

**Get all rooms for a hotel**
```bash
curl http://localhost:5001/rooms?hotel_id=<hotel_id>
```

**Get only available rooms**
```bash
curl http://localhost:5001/rooms?available=true
```

**Update room availability**
```bash
curl -X PATCH http://localhost:5001/rooms/<room_id>/availability \
  -H "Content-Type: application/json" \
  -d '{"is_available": false}'
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

## Dependencies

- **hotel-service** (port 5000) — must be running, rooms reference hotels via `hotel_id`