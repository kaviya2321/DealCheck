# -------------------------------------------------------------
# Stage 1: Build the React Frontend
# -------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Python Backend & Static Server
# -------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and ML models
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY .env.example .env

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port (Render/Railway dynamically sets $PORT, default 8000)
ENV PORT=8000
EXPOSE 8000

# Start unified FastAPI server
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
