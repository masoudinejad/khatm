# Backend API

## Development

### Setup
```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --all-extras
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_auth.py

# Run specific test
uv run pytest tests/test_auth.py::test_register_with_email

# Run tests in parallel (faster)
uv run pytest -n auto

# Run tests and generate HTML coverage report
uv run pytest --cov --cov-report=html
# Open htmlcov/index.html in browser
```

### Code Quality
```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Fix linting issues automatically
uv run ruff check --fix .
```

### Running the Server
```bash
# Development mode
uv run uvicorn src.main:app --reload

# Production mode
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```