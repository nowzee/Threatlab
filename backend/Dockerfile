# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim

# Install system dependencies for mysql-connector and other potential needs
RUN apt update && apt install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY backend/ .

# Copy built frontend from Stage 1
# This ensures that the frontend is built and placed where app.py expects it
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
