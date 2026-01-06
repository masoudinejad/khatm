# Backend API

Backend service for organizing collective recitation of Quran and Islamic texts.

## Setup
```bash
# Install dependencies
uv sync

# Create environment file
cp .env.example .env

# Run the server
uv run uvicorn src.main:app --reload
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.
