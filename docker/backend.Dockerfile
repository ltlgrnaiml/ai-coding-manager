# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

WORKDIR /app

# Install heavy dependencies first (rarely change) - separate layer for better caching
COPY backend/requirements-heavy.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-heavy.txt

# Install remaining dependencies (may change more often)
COPY backend/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy backend code and contracts
COPY backend/ ./backend/
COPY contracts/ ./contracts/

# Copy main package files
COPY pyproject.toml README.md uv.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install the main package
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
