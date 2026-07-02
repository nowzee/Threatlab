#!/usr/bin/env bash
# ============================================================================
#  Threatlab Honeypot Agent Installer
#  Downloads, configures, starts AND enables-at-boot a honeypot agent.
#
#  Run it (as root). You'll be asked to pick Docker or System (systemd):
#    curl -ksSL https://your-server/api/agent/install/ID | sudo bash
#
#  Skip the prompt with an explicit method:
#    curl -ksSL https://your-server/api/agent/install/ID | sudo bash -s -- --method docker
#    curl -ksSL https://your-server/api/agent/install/ID | sudo bash -s -- --method direct
#
#  Uninstall:
#    curl -ksSL https://your-server/api/agent/install/ID | sudo bash -s -- --uninstall
# ============================================================================

set -euo pipefail

# ====================== CONFIGURATION (injected by server) ======================
AGENT_ID="{{AGENT_ID}}"
AGENT_TOKEN="{{AGENT_TOKEN}}"
SERVER_URL="{{SERVER_URL}}"
SERVICE_TYPE="{{SERVICE_TYPE}}"
AGENT_NAME="{{AGENT_NAME}}"
BANNER="{{BANNER}}"
AGENT_PORTS="{{PORTS}}"   # space-separated, e.g. "22 2222"
# ================================================================================

# Defaults
INSTALL_METHOD=""
INSTALL_DIR="/opt/threatlabs-agent"
SERVICE_NAME="threatlabs-agent"
LOG_FILE="/var/log/threatlabs-agent.log"
IMAGE_NAME="threatlabs-agent-${AGENT_ID}"
CONTAINER_NAME="threatlabs-agent-${AGENT_ID}"
ASSUME_YES="0"   # set by --yes/-y to skip the "install dependencies?" prompt

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

# ====================== HELPERS ======================
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
check_command() { command -v "$1" &>/dev/null; }

# ---- Progress bar ----
STEP_CURRENT=0
STEP_TOTAL=1
progress_bar() {
    local label="$1" width=28 i bar=""
    local pct=$(( STEP_CURRENT * 100 / STEP_TOTAL ))
    local filled=$(( STEP_CURRENT * width / STEP_TOTAL ))
    for ((i = 0; i < width; i++)); do
        if [ "$i" -lt "$filled" ]; then bar+="#"; else bar+="-"; fi
    done
    printf "\r  ${CYAN}[%s]${NC} %3d%%  %-36s" "$bar" "$pct" "$label"
    # Use if/fi (not '[ ] && ...') so this never returns non-zero, which would
    # abort the script under `set -e` when it isn't the final step.
    if [ "$STEP_CURRENT" -ge "$STEP_TOTAL" ]; then printf "\n"; fi
    return 0
}
# run_step "label" command [args...] : advance the bar then run the command.
run_step() {
    local label="$1"; shift
    STEP_CURRENT=$(( STEP_CURRENT + 1 ))
    progress_bar "${label}"
    "$@"
}

banner() {
    echo -e "${CYAN}"
    echo "+--------------------------------------------------+"
    echo "|          Threatlabs Agent Installer              |"
    echo "|          Honeypot Deployment Tool                |"
    echo "+--------------------------------------------------+"
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
        OS_ID="${ID:-unknown}"; OS_NAME="${PRETTY_NAME:-unknown}"
    elif [ -f /etc/redhat-release ]; then
        OS_ID="rhel"; OS_NAME=$(cat /etc/redhat-release)
    else
        OS_ID="unknown"; OS_NAME="Unknown"
    fi
    log_info "Detected OS: ${OS_NAME}"
}

choose_auto_method() {
    if check_command docker; then echo "docker"; else echo "direct"; fi
}

# Ask the user before installing missing dependencies. Works when piped
# (curl | bash) by talking to /dev/tty. Returns 0 = proceed, 1 = declined.
# Bypassed with --yes, and auto-proceeds if there is no terminal at all.
confirm_install() {
    if [ "${ASSUME_YES}" = "1" ]; then return 0; fi
    if ! { true >/dev/tty; } 2>/dev/null; then return 0; fi
    {
        echo ""
        echo -e "${YELLOW}$1${NC}"
        printf "Install these now? [Y/n] "
    } >/dev/tty
    local ans=""
    read -r ans </dev/tty || ans=""
    case "${ans}" in
        n|N|no|NO|non|Non) return 1 ;;
        *) return 0 ;;
    esac
}

# Ask the user to choose Docker vs System. Works even when piped (curl | bash)
# by talking to the controlling terminal /dev/tty. Falls back to auto if there
# is no terminal at all (cron / CI).
prompt_method() {
    if ! { true >/dev/tty; } 2>/dev/null; then
        INSTALL_METHOD="$(choose_auto_method)"
        log_info "No interactive terminal — auto-selected method: ${INSTALL_METHOD}"
        return
    fi
    {
        echo ""
        echo -e "${BOLD}Choose the installation type:${NC}"
        echo ""
        echo -e "  ${GREEN}1)${NC} Docker    - isolated container (recommended)"
        echo -e "  ${GREEN}2)${NC} System    - native systemd service"
        echo ""
        printf "Choice [1-2] (default: 1): "
    } >/dev/tty
    local choice=""
    read -r choice </dev/tty || choice=""
    case "${choice}" in
        2) INSTALL_METHOD="direct" ;;
        *) INSTALL_METHOD="docker" ;;
    esac
}

# ====================== DEPENDENCY / WORK STEPS (quiet: driven by the bar) ======================
ensure_python_env() {
    # Ensure python3 + venv + pip are present (idempotent). On Ubuntu/Debian
    # python3 exists by default but python3-venv / python3-pip usually do NOT,
    # so we always (re)install them here. Failures are tolerated, then checked.
    case "${OS_ID}" in
        ubuntu|debian)
            apt-get update -qq >/dev/null 2>&1 || true
            DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv python3-pip >/dev/null 2>&1 || true ;;
        centos|rhel|fedora|rocky|alma)
            if check_command dnf; then dnf install -y -q python3 python3-pip >/dev/null 2>&1 || true
            else yum install -y -q python3 python3-pip >/dev/null 2>&1 || true; fi ;;
        alpine)
            apk add --no-cache python3 py3-pip >/dev/null 2>&1 || true ;;
        *)
            if check_command apt-get; then apt-get update -qq >/dev/null 2>&1 || true; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv python3-pip >/dev/null 2>&1 || true
            elif check_command dnf; then dnf install -y -q python3 python3-pip >/dev/null 2>&1 || true
            elif check_command yum; then yum install -y -q python3 python3-pip >/dev/null 2>&1 || true
            else apk add --no-cache python3 py3-pip >/dev/null 2>&1 || true; fi ;;
    esac
    if ! check_command python3; then
        echo; log_error "Python 3 is required but could not be installed. Install it and re-run."; exit 1
    fi
}

install_python_deps() {
    # Prefer an isolated venv (avoids PEP 668 "externally-managed" errors on
    # Ubuntu 24.04 / Debian 12). Fall back to system pip if venv is unavailable.
    PYTHON_BIN=""
    python3 -m venv "${INSTALL_DIR}/venv" >/dev/null 2>&1 || true
    if [ -x "${INSTALL_DIR}/venv/bin/pip" ]; then
        "${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
        if "${INSTALL_DIR}/venv/bin/pip" install --quiet paramiko requests >/dev/null 2>&1; then
            PYTHON_BIN="${INSTALL_DIR}/venv/bin/python3"
            return 0
        fi
    fi
    # Fallbacks: system pip (with and without --break-system-packages).
    if pip3 install --quiet --break-system-packages paramiko requests >/dev/null 2>&1 \
       || python3 -m pip install --quiet --break-system-packages paramiko requests >/dev/null 2>&1 \
       || pip3 install --quiet paramiko requests >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
        return 0
    fi
    echo; log_error "Could not install Python dependencies (paramiko, requests). Check network / pip."; exit 1
}

download_agent() {
    mkdir -p "${INSTALL_DIR}"
    # -k: the server uses a self-signed certificate.
    if check_command curl; then
        curl -ksSL -o "${INSTALL_DIR}/agent.py" "${SERVER_URL}/api/agent/download/${AGENT_ID}" >/dev/null 2>&1
    elif check_command wget; then
        wget -q --no-check-certificate -O "${INSTALL_DIR}/agent.py" "${SERVER_URL}/api/agent/download/${AGENT_ID}"
    else
        echo; log_error "Neither curl nor wget found. Please install one."; exit 1
    fi
    if [ ! -s "${INSTALL_DIR}/agent.py" ]; then
        echo; log_error "Failed to download agent script (empty file)"; exit 1
    fi
    chmod 600 "${INSTALL_DIR}/agent.py"
}

port_args() {
    # Map every user-chosen port (host -> container, same number).
    local args="" p
    for p in ${AGENT_PORTS}; do args="${args} -p ${p}:${p}"; done
    echo "${args}"
}

docker_build_image() {
    {
        cat <<'DOCKEREOF'
FROM python:3.11-alpine
RUN apk add --no-cache libffi openssl \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir paramiko requests
WORKDIR /app
COPY agent.py /app/agent.py
DOCKEREOF
        echo "EXPOSE ${AGENT_PORTS}"
        cat <<'DOCKEREOF'
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "agent.py" >/dev/null 2>&1 || exit 1
CMD ["python3", "-u", "/app/agent.py"]
DOCKEREOF
    } > "${INSTALL_DIR}/Dockerfile"
    docker build -t "${IMAGE_NAME}" "${INSTALL_DIR}" >"${INSTALL_DIR}/build.log" 2>&1 || {
        echo; log_error "Docker build failed. Last lines:"; tail -n 20 "${INSTALL_DIR}/build.log"; exit 1;
    }
}

docker_run_container() {
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    # shellcheck disable=SC2046
    docker run -d --name "${CONTAINER_NAME}" --restart unless-stopped $(port_args) "${IMAGE_NAME}" >/dev/null
}

create_systemd_service() {
    # PYTHON_BIN is set by install_python_deps (venv or system python that has
    # the deps). Fall back to system python3 just in case.
    local py="${PYTHON_BIN:-$(command -v python3)}"
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<SERVICEEOF
[Unit]
Description=Threatlabs Honeypot Agent (${AGENT_NAME})
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${py} ${INSTALL_DIR}/agent.py
Restart=always
RestartSec=10
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

[Install]
WantedBy=multi-user.target
SERVICEEOF
}

enable_systemd_service() {
    systemctl daemon-reload
    systemctl enable --now "${SERVICE_NAME}" >/dev/null 2>&1
}

# ====================== INSTALL METHODS ======================
install_docker() {
    STEP_CURRENT=0; STEP_TOTAL=4
    echo -e "${BOLD}Installing via Docker...${NC}"
    if ! check_command docker; then
        echo; log_error "Docker is not installed. Install Docker first, or re-run and choose option 2 (System)."; exit 1
    fi
    run_step "Checking Docker" true
    systemctl enable --now docker >/dev/null 2>&1 || true
    run_step "Downloading agent" download_agent
    run_step "Building image" docker_build_image
    run_step "Starting container" docker_run_container

    log_success "Container started and set to auto-restart: ${CONTAINER_NAME}"
    echo ""
    log_info "Useful commands:"
    echo "  docker logs -f ${CONTAINER_NAME}    # View logs"
    echo "  docker restart ${CONTAINER_NAME}    # Restart"
    echo "  docker rm -f ${CONTAINER_NAME}      # Remove agent"
}

install_direct() {
    STEP_CURRENT=0; STEP_TOTAL=5
    echo -e "${BOLD}Installing natively (systemd)...${NC}"

    # Detect missing SYSTEM packages (installed via the package manager). The
    # Python libs (paramiko, requests) are installed into an isolated venv and
    # don't touch the system, so they are NOT listed in this prompt.
    local need=""
    if ! check_command python3; then
        need="python3 python3-venv python3-pip"
    else
        python3 -m venv --help  >/dev/null 2>&1 || need="${need} python3-venv"
        python3 -m pip --version >/dev/null 2>&1 || need="${need} python3-pip"
    fi
    if [ -n "${need}" ]; then
        if ! confirm_install "The following system packages will be installed:${need}"; then
            echo; log_error "Cancelled. These packages are required to run the agent (or re-run with --yes)."; exit 1
        fi
    fi

    run_step "Preparing Python" ensure_python_env
    run_step "Downloading agent" download_agent
    run_step "Installing dependencies" install_python_deps
    run_step "Creating systemd service" create_systemd_service
    run_step "Enabling and starting" enable_systemd_service

    log_success "Service created, started and enabled at boot: ${SERVICE_NAME}"
    echo ""
    log_info "Useful commands:"
    echo "  systemctl status ${SERVICE_NAME}     # Check status"
    echo "  journalctl -u ${SERVICE_NAME} -f     # View logs"
    echo "  systemctl restart ${SERVICE_NAME}    # Restart"
}

install_manual() {
    STEP_CURRENT=0; STEP_TOTAL=1
    echo -e "${BOLD}Downloading files only...${NC}"
    run_step "Downloading agent" download_agent
    log_success "Agent downloaded to ${INSTALL_DIR}/"
    echo ""
    log_info "To run manually:  cd ${INSTALL_DIR} && pip3 install paramiko requests && sudo python3 agent.py"
    log_info "(the agent writes its own honeypot_config.json on first run)"
}

uninstall() {
    log_warn "Uninstalling Threatlabs agent..."
    if systemctl list-unit-files 2>/dev/null | grep -q "${SERVICE_NAME}.service"; then
        systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
        systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload 2>/dev/null || true
        log_success "Systemd service removed"
    fi
    if check_command docker; then
        docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 && log_success "Docker container removed" || true
        docker rmi "${IMAGE_NAME}" >/dev/null 2>&1 && log_success "Docker image removed" || true
    fi
    if [ -d "${INSTALL_DIR}" ]; then rm -rf "${INSTALL_DIR}"; log_success "Removed ${INSTALL_DIR}"; fi
    rm -f "${LOG_FILE}"
    log_success "Uninstall complete"
}

# ====================== MAIN ======================
main() {
    banner

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --method|-m) INSTALL_METHOD="$2"; shift 2 ;;
            --dir|-d)    INSTALL_DIR="$2"; shift 2 ;;
            --yes|-y)    ASSUME_YES="1"; shift ;;
            --uninstall) INSTALL_METHOD="uninstall"; shift ;;
            --help|-h)
                echo "Usage: $0 [--method docker|direct|manual|auto] [--dir DIR] [--yes] [--uninstall]"
                exit 0 ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done

    check_root
    detect_os

    # No method on the command line: ask Docker vs System (interactive), or
    # auto-select if there is no terminal.
    if [ -z "${INSTALL_METHOD}" ]; then
        prompt_method
    fi
    [ "${INSTALL_METHOD}" = "auto" ] && INSTALL_METHOD="$(choose_auto_method)"

    echo ""
    log_info "Installation method: ${INSTALL_METHOD}"
    echo ""

    case "${INSTALL_METHOD}" in
        docker)    install_docker ;;
        direct)    install_direct ;;
        manual)    install_manual ;;
        uninstall) uninstall ;;
        *) log_error "Unknown method: ${INSTALL_METHOD}"; exit 1 ;;
    esac

    echo ""
    echo -e "${GREEN}+--------------------------------------------------+${NC}"
    echo -e "${GREEN}|          Installation Complete!                  |${NC}"
    echo -e "${GREEN}+--------------------------------------------------+${NC}"
    echo ""
    echo -e "  Agent ID:     ${BOLD}${AGENT_ID}${NC}"
    echo -e "  Install dir:  ${BOLD}${INSTALL_DIR}${NC}"
    echo -e "  Method:       ${BOLD}${INSTALL_METHOD}${NC}"
    echo ""
    echo -e "  ${GREEN}The agent is running and will restart automatically at boot.${NC}"
    echo ""
}

main "$@"
