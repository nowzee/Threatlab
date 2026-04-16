FROM python:3.11-alpine
LABEL authors="Threatlab"

# Install dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && pip install --no-cache-dir \
    paramiko \
    requests

# Create app directory
WORKDIR /app

# Copy honeypot agent and config
COPY agent.py /app/agent.py
COPY honeypot_config.json /app/honeypot_config.json

# Expose ports for honeypot services
EXPOSE 22 21

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python" || exit 1

# Start honeypot agent
CMD ["python3", "/app/agent.py"]
