# Khatm Service 📖

A simple backend service for organizing collective Quran recitation (Khatm). Allows groups to coordinate reading the entire Quran by dividing it into portions.

## Features

- User authentication (email or phone number)
- Create and manage Khatm sessions
- Support for Juz (30), Hezb (60), or Quarter (240) portions
- Claim and track completion of portions
- Progress statistics
- Multi-language support

## Quick Start

```bash
# Install dependencies
uv pip install fastapi uvicorn pyjwt

# Run the server
uv run python main.py
```

API will be available at `http://localhost:8000`

## API Documentation

Interactive documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Basic Usage

### 1. Register a user
```bash
POST /auth/register
{
  "name": "Ahmed",
  "email": "ahmed@example.com",
  "password": "yourpassword"
}
```

### 2. Create a Khatm
```bash
POST /khatms
Authorization: Bearer <token>
{
  "title": "Ramadan Khatm 2024",
  "portion_type": "juz"
}
```

### 3. Join and claim portions
```bash
POST /khatms/{id}/join
POST /khatms/{id}/assign
{
  "portion_number": 5
}
```

### 4. Mark as complete
```bash
PUT /khatms/{id}/portions/{number}/complete
```

## Phone Number Format

Use international format: `+491234567890` or `+49 123 456 7890`

## Production Setup

1. Set a secure SECRET_KEY:
   ```bash
   export SECRET_KEY="your-secure-random-key"
   ```

2. Consider using PostgreSQL instead of SQLite

3. Deploy with Gunicorn:
   ```bash
   uv pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

## Tech Stack

- FastAPI (Python)
- SQLite database
- JWT authentication

## License

MIT
