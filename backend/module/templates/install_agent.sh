#!/usr/bin/env bash
# ============================================================================
#  Threatlabs Honeypot Agent Installer
#  Installs and configures a honeypot agent on the target system.
#
#  Usage:
#    curl -sSL https://your-server/api/agent/install/ID | sudo bash
#    curl -sSL https://your-server/api/agent/install/ID | sudo bash -s -- --method docker
#    curl -sSL https://your-server/api/agent/install/ID | sudo bash -s -- --method direct
#    curl -sSL https://your-server/api/agent/install/ID | sudo bash -s -- --method manual
# ============================================================================

set -euo pipefail

# ====================== CONFIGURATION (injected by server) ======================
AGENT_ID="{{AGENT_ID}}"
AGENT_TOKEN="{{AGENT_TOKEN}}"
SERVER_URL="{{SERVER_URL}}"
SERVICE_TYPE="{{SERVICE_TYPE}}"
AGENT_NAME="{{AGENT_NAME}}"
BANNER="{{BANNER}}"
# ================================================================================

# Defaults
INSTALL_METHOD=""
INSTALL_DIR="/opt/threatlabs-agent"
SERVICE_NAME="threatlabs-agent"
LOG_FILE="/var/log/threatlabs-agent.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ====================== HELPERS ======================

log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║          Threatlabs Agent Installer              ║"
    echo "║          Honeypot Deployment Tool                ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "  Agent:        ${BOLD}${AGENT_NAME}${NC}"
    echo -e "  Type:         ${BOLD}${SERVICE_TYPE}${NC}"
    echo -e "  Server:       ${BOLD}${SERVER_URL}${NC}"
    echo -e "  Agent ID:     ${BOLD}${AGENT_ID}${NC}"
    echo ""
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID="${ID}"
        OS_VERSION="${VERSION_ID:-unknown}"
        OS_NAME="${PRETTY_NAME}"
    elif [ -f /etc/redhat-release ]; then
        OS_ID="rhel"
        OS_NAME=$(cat /etc/redhat-release)
    else
        OS_ID="unknown"
        OS_NAME="Unknown"
    fi
    log_info "Detected OS: ${OS_NAME}"
}

check_command() {
    command -v "$1" &>/dev/null
}

# ====================== DEPENDENCY INSTALLATION ======================

install_python() {
    log_info "Installing Python 3 and pip..."

    case "${OS_ID}" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq python3 python3-pip python3-venv >/dev/null 2>&1
            ;;
        centos|rhel|fedora|rocky|alma)
            if check_command dnf; then
                dnf install -y -q python3 python3-pip >/dev/null 2>&1
            else
                yum install -y -q python3 python3-pip >/dev/null 2>&1
            fi
            ;;
        alpine)
            apk add --no-cache python3 py3-pip >/dev/null 2>&1
            ;;
        *)
            log_warn "Unknown OS '${OS_ID}'. Attempting generic install..."
            if check_command apt-get; then
                apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv >/dev/null 2>&1
            elif check_command dnf; then
                dnf install -y -q python3 python3-pip >/dev/null 2>&1
            elif check_command yum; then
                yum install -y -q python3 python3-pip >/dev/null 2>&1
            else
                log_error "Cannot install Python. Please install Python 3.8+ manually."
                exit 1
            fi
            ;;
    esac

    log_success "Python 3 installed"
}

install_python_deps() {
    log_info "Installing Python dependencies (paramiko, requests)..."

    # Use venv to avoid breaking system packages
    python3 -m venv "${INSTALL_DIR}/venv" 2>/dev/null || true
    if [ -f "${INSTALL_DIR}/venv/bin/pip" ]; then
        "${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade pip
        "${INSTALL_DIR}/venv/bin/pip" install --quiet paramiko requests
    else
        pip3 install --quiet --break-system-packages paramiko requests 2>/dev/null || \
        pip3 install --quiet paramiko requests
    fi

    log_success "Python dependencies installed"
}

# ====================== AGENT DOWNLOAD ======================

download_agent() {
    log_info "Downloading agent script from server..."

    mkdir -p "${INSTALL_DIR}"

    # -k / --no-check-certificate: the server uses a self-signed certificate.
    if check_command curl; then
        curl -ksSL -o "${INSTALL_DIR}/agent.py" \
            "${SERVER_URL}/api/agent/download/${AGENT_ID}"
    elif check_command wget; then
        wget -q --no-check-certificate -O "${INSTALL_DIR}/agent.py" \
            "${SERVER_URL}/api/agent/download/${AGENT_ID}"
    else
        log_error "Neither curl nor wget found. Please install one."
        exit 1
    fi

    if [ ! -s "${INSTALL_DIR}/agent.py" ]; then
        log_error "Failed to download agent script (empty file)"
        exit 1
    fi

    chmod 600 "${INSTALL_DIR}/agent.py"
    log_success "Agent script downloaded to ${INSTALL_DIR}/agent.py"
}

write_config() {
    log_info "Writing agent configuration..."

    cat > "${INSTALL_DIR}/honeypot_config.json" <<CONFIGEOF
{
    "agent_id": ${AGENT_ID},
    "agent_token": "${AGENT_TOKEN}",
    "server_url": "${SERVER_URL}",
    "features": {
        "ssh_enabled": $([ "${SERVICE_TYPE}" = "ssh" ] && echo "true" || echo "false"),
        "ftp_enabled": $([ "${SERVICE_TYPE}" = "ftp" ] && echo "true" || echo "false"),
        "port_scan_detection": true,
        "auth_detection": true
    },
    "ssh": {
        "host": "0.0.0.0",
        "port": 22,
        "banner": "${BANNER}",
        "host_key_file": "${INSTALL_DIR}/ssh_host_key.pem"
    },
    "ftp": {
        "host": "0.0.0.0",
        "port": 21,
        "banner": "220 FTP server ready"
    },
    "reporting": {
        "interval": 30,
        "endpoint": "/api/agent/report"
    },
    "port_scan": {
        "threshold": 5,
        "time_window": 10
    }
}
CONFIGEOF

    chmod 600 "${INSTALL_DIR}/honeypot_config.json"
    log_success "Configuration written to ${INSTALL_DIR}/honeypot_config.json"
}

# ====================== INSTALL METHODS ======================

install_docker() {
    log_info "Installing via Docker..."

    if ! check_command docker; then
        log_info "Docker not found, installing..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable --now docker
        log_success "Docker installed"
    fi

    # Download agent first
    download_agent
    write_config

    # Create Dockerfile
    cat > "${INSTALL_DIR}/Dockerfile" <<'DOCKEREOF'
FROM python:3.11-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir paramiko requests

WORKDIR /app
COPY agent.py /app/agent.py
COPY honeypot_config.json /app/honeypot_config.json

EXPOSE 22 21

CMD ["python3", "/app/agent.py"]
DOCKEREOF

    # Build and run
    log_info "Building Docker image..."
    docker build -t "threatlabs-agent-${AGENT_ID}" "${INSTALL_DIR}" --quiet

    # Stop existing container if any
    docker rm -f "threatlabs-agent-${AGENT_ID}" 2>/dev/null || true

    log_info "Starting container..."
    local ports=""
    if [ "${SERVICE_TYPE}" = "ssh" ]; then
        ports="-p 22:22"
    elif [ "${SERVICE_TYPE}" = "ftp" ]; then
        ports="-p 21:21"
    else
        ports="-p 22:22 -p 21:21"
    fi

    docker run -d \
        --name "threatlabs-agent-${AGENT_ID}" \
        --restart unless-stopped \
        ${ports} \
        "threatlabs-agent-${AGENT_ID}"

    log_success "Docker container started: threatlabs-agent-${AGENT_ID}"
    echo ""
    log_info "Useful commands:"
    echo "  docker logs -f threatlabs-agent-${AGENT_ID}    # View logs"
    echo "  docker stop threatlabs-agent-${AGENT_ID}       # Stop agent"
    echo "  docker start threatlabs-agent-${AGENT_ID}      # Start agent"
    echo "  docker rm -f threatlabs-agent-${AGENT_ID}      # Remove agent"
}

install_direct() {
    log_info "Installing directly on host with systemd..."

    # Install dependencies
    if ! check_command python3; then
        install_python
    fi

    download_agent
    install_python_deps
    write_config

    # Determine Python path (venv or system)
    if [ -f "${INSTALL_DIR}/venv/bin/python3" ]; then
        PYTHON_BIN="${INSTALL_DIR}/venv/bin/python3"
    else
        PYTHON_BIN=$(which python3)
    fi

    # Create systemd service
    log_info "Creating systemd service..."

    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<SERVICEEOF
[Unit]
Description=Threatlabs Honeypot Agent (${AGENT_NAME})
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${PYTHON_BIN} ${INSTALL_DIR}/agent.py
Restart=always
RestartSec=10
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=${INSTALL_DIR} ${LOG_FILE}
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
SERVICEEOF

    # Enable and start
    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
    systemctl start "${SERVICE_NAME}"

    log_success "Systemd service created and started: ${SERVICE_NAME}"
    echo ""
    log_info "Useful commands:"
    echo "  systemctl status ${SERVICE_NAME}     # Check status"
    echo "  journalctl -u ${SERVICE_NAME} -f     # View logs"
    echo "  systemctl restart ${SERVICE_NAME}    # Restart"
    echo "  systemctl stop ${SERVICE_NAME}       # Stop"
    echo "  cat ${LOG_FILE}                      # View log file"
}

install_manual() {
    log_info "Manual installation (download only)..."

    download_agent
    write_config

    log_success "Agent files downloaded to ${INSTALL_DIR}/"
    echo ""
    log_info "To run manually:"
    echo "  cd ${INSTALL_DIR}"
    echo "  pip3 install paramiko requests"
    echo "  sudo python3 agent.py"
}

# ====================== UNINSTALL ======================

uninstall() {
    log_warn "Uninstalling Threatlabs agent..."

    # Stop and remove systemd service
    if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
        systemctl stop "${SERVICE_NAME}"
        systemctl disable "${SERVICE_NAME}"
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        log_success "Systemd service removed"
    fi

    # Stop and remove Docker container
    if check_command docker; then
        docker rm -f "threatlabs-agent-${AGENT_ID}" 2>/dev/null && \
            log_success "Docker container removed"
        docker rmi "threatlabs-agent-${AGENT_ID}" 2>/dev/null && \
            log_success "Docker image removed"
    fi

    # Remove files
    if [ -d "${INSTALL_DIR}" ]; then
        rm -rf "${INSTALL_DIR}"
        log_success "Removed ${INSTALL_DIR}"
    fi

    rm -f "${LOG_FILE}"
    log_success "Uninstall complete"
}

# ====================== INTERACTIVE MENU ======================

select_method() {
    echo ""
    echo -e "${BOLD}Select installation method:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Docker        - Run in an isolated container (recommended)"
    echo -e "  ${GREEN}2)${NC} Direct        - Install on host with systemd service"
    echo -e "  ${GREEN}3)${NC} Manual        - Download files only"
    echo -e "  ${RED}4)${NC} Uninstall     - Remove existing installation"
    echo ""
    read -rp "Choice [1-4]: " choice

    case "${choice}" in
        1) INSTALL_METHOD="docker" ;;
        2) INSTALL_METHOD="direct" ;;
        3) INSTALL_METHOD="manual" ;;
        4) INSTALL_METHOD="uninstall" ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
}

# ====================== MAIN ======================

main() {
    banner

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --method|-m)
                INSTALL_METHOD="$2"
                shift 2
                ;;
            --dir|-d)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --uninstall)
                INSTALL_METHOD="uninstall"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --method, -m METHOD   Installation method: docker, direct, manual"
                echo "  --dir, -d DIR         Installation directory (default: /opt/threatlabs-agent)"
                echo "  --uninstall           Remove existing installation"
                echo "  --help, -h            Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    check_root
    detect_os

    # Interactive selection if no method specified
    if [ -z "${INSTALL_METHOD}" ]; then
        select_method
    fi

    echo ""
    log_info "Installation method: ${INSTALL_METHOD}"
    echo ""

    case "${INSTALL_METHOD}" in
        docker)     install_docker ;;
        direct)     install_direct ;;
        manual)     install_manual ;;
        uninstall)  uninstall ;;
        *)
            log_error "Unknown method: ${INSTALL_METHOD}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          Installation Complete!                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Agent ID:     ${BOLD}${AGENT_ID}${NC}"
    echo -e "  Server:       ${BOLD}${SERVER_URL}${NC}"
    echo -e "  Install dir:  ${BOLD}${INSTALL_DIR}${NC}"
    echo -e "  Method:       ${BOLD}${INSTALL_METHOD}${NC}"
    echo ""
}

main "$@"
