# hotel-service

Manages hotel data for the Hotel Booking App. This is the foundational service — other services like **room-service** and **search-service** depend on hotel data.

Runs on port **5000**.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hotels` | List all hotels |
| GET | `/hotels/<hotel_id>` | Get one hotel by ID |
| POST | `/hotels` | Create a new hotel |
| PUT | `/hotels/<hotel_id>` | Update a hotel |
| DELETE | `/hotels/<hotel_id>` | Delete a hotel |
| GET | `/health` | Health check |

## Hotel Schema

```json
{
  "name": "string (required)",
  "location": "string (required)",
  "star_rating": "number (required)",
  "amenities": ["wifi", "pool", "gym"],
  "description": "string",
  "phone": "string",
  "email": "string"
}
```

## Example Requests

**Create a hotel**
```bash
curl -X POST http://localhost:5000/hotels \
  -H "Content-Type: application/json" \
  -d '{"name": "Grand Hotel", "location": "New York", "star_rating": 5}'
```

**Get all hotels**
```bash
curl http://localhost:5000/hotels
```

**Update a hotel**
```bash
curl -X PUT http://localhost:5000/hotels/<hotel_id> \
  -H "Content-Type: application/json" \
  -d '{"star_rating": 4}'
```

**Delete a hotel**
```bash
curl -X DELETE http://localhost:5000/hotels/<hotel_id>
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
MONGO_URL=mongodb://localhost:27017 python app.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URL` | `mongodb://localhost:27017/` | MongoDB connection string |