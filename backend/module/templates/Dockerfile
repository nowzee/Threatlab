# ============================================================================
#  Threatlab Honeypot Agent — lightweight container image.
#
#  Based on python:3.11-alpine. cryptography / paramiko / cffi all publish
#  musllinux wheels, so NO compiler/build toolchain is needed — only the tiny
#  runtime libs. Keeps the final image small and the build fast & reliable.
# ============================================================================
FROM python:3.11-alpine

LABEL org.opencontainers.image.title="Threatlab Honeypot Agent" \
      org.opencontainers.image.description="Self-contained honeypot agent (SSH/FTP emulation)"

# Runtime libraries only (no gcc/musl-dev): wheels are used for the Python deps.
RUN apk add --no-cache libffi openssl \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir paramiko requests

WORKDIR /app
# Only the agent is copied. Its full configuration (server URL, token, auth
# whitelist, …) is baked into the script by the server, so no separate config
# file is needed — the agent writes honeypot_config.json itself on first run.
COPY agent.py /app/agent.py

# Honeypot service ports (SSH / FTP). Mapped to the host at run time.
EXPOSE 22 21

# Consider the container unhealthy if the agent process has died.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "agent.py" >/dev/null 2>&1 || exit 1

# -u = unbuffered stdout so `docker logs` shows activity in real time.
CMD ["python3", "-u", "/app/agent.py"]
