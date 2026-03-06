# user-service

Manages users for the Hotel Booking App. Handles registration, login, and user profiles. **booking-service** depends on this service.

Runs on port **5002**.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Register a new user |
| GET | `/users` | List all users |
| GET | `/users/<user_id>` | Get one user |
| PUT | `/users/<user_id>` | Update a user |
| DELETE | `/users/<user_id>` | Delete a user |
| POST | `/users/login` | Login |
| GET | `/health` | Health check |

## User Schema

```json
{
  "name": "string (required)",
  "email": "string (required, unique)",
  "password": "string (required, stored as SHA-256 hash)",
  "phone": "string",
  "address": "string",
  "role": "string (guest or admin, default: guest)"
}
```

## Example Requests

**Register a user**
```bash
curl -X POST http://localhost:5002/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "password": "secret123"}'
```

**Login**
```bash
curl -X POST http://localhost:5002/users/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secret123"}'
```

**Get all users**
```bash
curl http://localhost:5002/users
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

## Notes

- Passwords are never returned in any response
- Passwords are stored as SHA-256 hashes
- booking-service will reference users via `user_id`