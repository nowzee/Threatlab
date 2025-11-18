#!/usr/bin/env python3
"""
SSH Honeypot Agent
This agent simulates an SSH server to collect attack data and report to the Threatlabs server.
"""

import paramiko
import socket
import threading
import time
import requests
import os
import sys
from datetime import datetime
import logging
import json
from collections import defaultdict

# ========== CONFIGURATION ==========
CONFIG_FILE = "honeypot_config.json"

# Default configuration (injected by server)
DEFAULT_CONFIG = $default_config_json

# Global configuration
config = {}

# ===================================

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Storage for collected attacks
collected_attacks = []
attacks_lock = threading.Lock()

# Port scan detection
port_scan_tracker = defaultdict(list)
port_scan_lock = threading.Lock()


def setup_config():
    """Load or create configuration file"""
    global config

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            config = DEFAULT_CONFIG.copy()
    else:
        config = DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Configuration file created: {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")

    return config

class SSHServerHandler(paramiko.ServerInterface):
    """Handles SSH authentication attempts"""

    def __init__(self, client_address):
        self.client_address = client_address
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        """Capture username/password attempts and always reject"""
        if not config.get('features', {}).get('auth_detection', True):
            return paramiko.AUTH_FAILED

        logger.info(f"SSH auth attempt from {self.client_address[0]}: {username}:{password}")

        # Collect attack data
        attack_data = {
            'source_ip': self.client_address[0],
            'source_port': self.client_address[1],
            'target_port': config.get('ssh', {}).get('port', 22),
            'username_attempt': username,
            'password_attempt': password,
            'timestamp': datetime.now().isoformat(),
            'service_type': 'ssh',
            'attack_type': 'auth_attempt'
        }

        with attacks_lock:
            collected_attacks.append(attack_data)

        # Always reject authentication
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """Reject public key authentication"""
        logger.info(f"Public key auth attempt from {self.client_address[0]}: {username}")
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        """Advertise password authentication"""
        return 'password'

    def check_channel_request(self, kind, chanid):
        """Accept channel requests"""
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


def get_ip_geolocation(ip_address):
    """Get geolocation data for an IP address"""
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country_name': data.get('country_name'),
                'country_code': data.get('country_code'),
                'city': data.get('city'),
                'region': data.get('region')
            }
    except Exception as e:
        logger.warning(f"Failed to get geolocation for {ip_address}: {e}")

    return {
        'country_name': None,
        'country_code': None,
        'city': None,
        'region': None
    }


def report_attacks():
    """Send collected attacks to the Threatlabs server"""
    while True:
        time.sleep(config.get('reporting', {}).get('interval', 30))

        with attacks_lock:
            if not collected_attacks:
                continue

            # Copy and clear the list
            attacks_to_send = collected_attacks.copy()
            collected_attacks.clear()

        logger.info(f"Reporting {len(attacks_to_send)} attacks to server...")

        for attack in attacks_to_send:
            try:
                # Enrich with geolocation data
                if 'source_ip' in attack:
                    geo_data = get_ip_geolocation(attack['source_ip'])
                    attack.update(geo_data)

                # Add agent ID
                attack['agent_id'] = config.get('agent_id', 1)

                # Send to server
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {config.get("agent_token", "")}'
                }

                server_url = config.get('server_url', '')
                endpoint = config.get('reporting', {}).get('endpoint', '/api/agent/report')
                report_url = server_url + endpoint

                response = requests.post(
                    report_url,
                    json=attack,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    logger.info(f"Successfully reported attack: {attack.get('attack_type', 'unknown')}")
                else:
                    logger.error(f"Failed to report attack: {response.status_code} - {response.text}")
                    # Re-add to queue if failed
                    with attacks_lock:
                        collected_attacks.append(attack)

            except Exception as e:
                logger.error(f"Error reporting attack: {e}")
                # Re-add to queue if failed
                with attacks_lock:
                    collected_attacks.append(attack)


def load_or_generate_host_key():
    """Load existing host key or generate a new one"""
    host_key_file = config.get('ssh', {}).get('host_key_file', 'ssh_host_key.pem')
    if os.path.exists(host_key_file):
        try:
            logger.info(f"Loading host key from {host_key_file}")
            host_key = paramiko.RSAKey.from_private_key_file(host_key_file)
            logger.info("Host key loaded successfully")
            return host_key
        except Exception as e:
            logger.error(f"Failed to load host key: {e}")
            logger.info("Generating new host key...")
    else:
        logger.info("Host key file not found, generating new key...")

    # Generate new host key
    host_key = paramiko.RSAKey.generate(2048)

    # Save to file
    try:
        host_key.write_private_key_file(host_key_file)
        logger.info(f"Host key saved to {host_key_file}")
    except Exception as e:
        logger.error(f"Failed to save host key: {e}")

    return host_key


def handle_client_ssh(client_socket, client_address):
    """Handle individual SSH client connections"""
    try:

        # Create SSH transport
        transport = paramiko.Transport(client_socket)

        # Load host key from file for each connection
        host_key = load_or_generate_host_key()
        transport.add_server_key(host_key)

        # Set custom SSH banner
        ssh_banner = config.get('ssh', {}).get('banner', 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5')
        transport.local_version = ssh_banner

        # Start server with custom handler
        server_handler = SSHServerHandler(client_address)
        transport.start_server(server=server_handler)

        # Wait for authentication attempt
        channel = transport.accept(20)
        if channel is not None:
            channel.close()

    except paramiko.SSHException as e:
        logger.debug(f"SSH negotiation failed with {client_address[0]}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_address[0]}: {e}")
    finally:
        try:
            transport.close()
        except:
            pass


def handle_client_ftp(conn, addr):
    """Handle individual FTP client connections"""
    peer = f"{addr[0]}:{addr[1]}"

    try:

        # Send FTP banner
        ftp_banner = config.get('ftp', {}).get('banner', '220 FTP server ready')
        conn.sendall((ftp_banner + "\r\n").encode())

        username = None
        password = None
        buf = b""
        conn.settimeout(300)

        while True:
            data = conn.recv(4096)
            if not data:
                break

            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.rstrip(b"\r").decode(errors="ignore")

                if not line:
                    continue

                parts = line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "USER":
                    username = arg.strip()
                    conn.sendall(b"331 Password required\r\n")

                elif cmd == "PASS":
                    password = arg.strip()
                    conn.sendall(b"530 Login Authentication Failed\r\n")

                    # Log FTP authentication attempt
                    if config.get('features', {}).get('auth_detection', True):
                        logger.info(f"FTP auth attempt from {addr[0]}: {username}:{password}")

                        attack_data = {
                            'source_ip': addr[0],
                            'source_port': addr[1],
                            'target_port': config.get('ftp', {}).get('port', 21),
                            'username_attempt': username or "",
                            'password_attempt': password or "",
                            'timestamp': datetime.now().isoformat(),
                            'service_type': 'ftp',
                            'attack_type': 'auth_attempt'
                        }

                        with attacks_lock:
                            collected_attacks.append(attack_data)

                elif cmd == "OPTS":
                    conn.sendall(b"200 OPTS UTF8 command successful\r\n")

                else:
                    conn.sendall(b"500 Unknown command\r\n")

    except socket.timeout:
        pass
    except Exception as e:
        logger.error(f"Error handling FTP client {peer}: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

def start_ssh_honeypot():
    """Start the SSH honeypot server"""
    if not config.get('features', {}).get('ssh_enabled', True):
        logger.info("SSH honeypot is disabled in configuration")
        return

    ssh_host = config.get('ssh', {}).get('host', '0.0.0.0')
    ssh_port = config.get('ssh', {}).get('port', 22)

    logger.info(f"Starting SSH Honeypot on {ssh_host}:{ssh_port}")
    logger.info(f"Agent ID: {config.get('agent_id', 1)}")

    # Ensure host key exists
    load_or_generate_host_key()

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((ssh_host, ssh_port))
    except OSError as e:
        logger.error(f"Failed to bind to port {ssh_port}: {e}")
        logger.error("Make sure you have permission to bind to this port (use sudo for ports < 1024)")
        sys.exit(1)

    server_socket.listen(100)
    logger.info(f"SSH Honeypot listening on port {ssh_port}")

    # Accept connections
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            logger.info(f"SSH connection from {client_address[0]}:{client_address[1]}")

            # Handle client in separate thread
            client_thread = threading.Thread(
                target=handle_client_ssh,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        logger.info("Shutting down SSH honeypot...")
    finally:
        server_socket.close()

def start_ftp_honeypot():
    """Start the FTP honeypot server"""
    if not config.get('features', {}).get('ftp_enabled', True):
        logger.info("FTP honeypot is disabled in configuration")
        return

    ftp_host = config.get('ftp', {}).get('host', '0.0.0.0')
    ftp_port = config.get('ftp', {}).get('port', 21)

    logger.info(f"Starting FTP Honeypot on {ftp_host}:{ftp_port}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        s.bind((ftp_host, ftp_port))
    except OSError as e:
        logger.error(f"Failed to bind to port {ftp_port}: {e}")
        logger.error("Make sure you have permission to bind to this port (use sudo for ports < 1024)")
        sys.exit(1)

    s.listen(100)
    logger.info(f"FTP Honeypot listening on port {ftp_port}")

    try:
        while True:
            conn, addr = s.accept()
            logger.info(f"FTP connection from {addr[0]}:{addr[1]}")
            t = threading.Thread(target=handle_client_ftp, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        logger.info("Shutting down FTP honeypot...")
    finally:
        s.close()




if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Threatlabs Honeypot Agent")
    logger.info("="*60)

    # Setup configuration
    setup_config()

    # Start reporting thread
    reporter_thread = threading.Thread(target=report_attacks, daemon=True)
    reporter_thread.start()

    # Start honeypot services in separate threads
    services = []

    if config.get('features', {}).get('ssh_enabled', True):
        ssh_thread = threading.Thread(target=start_ssh_honeypot, daemon=True)
        ssh_thread.start()
        services.append(('SSH', ssh_thread))

    if config.get('features', {}).get('ftp_enabled', True):
        ftp_thread = threading.Thread(target=start_ftp_honeypot, daemon=True)
        ftp_thread.start()
        services.append(('FTP', ftp_thread))

    logger.info(f"Started {len(services)} honeypot service(s)")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down honeypot agent...")
        sys.exit(0)
