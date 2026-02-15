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

# Copy honeypot agents
COPY ssh_honeypot_agent.py /app/

# Expose ports for honeypot services
EXPOSE 22 21 139 445

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python" || exit 1

# Start all honeypots
CMD ["python3 /app/ssh_honeypot_agent"]