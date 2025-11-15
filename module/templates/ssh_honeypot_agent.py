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
import json
import sys
from datetime import datetime
import logging

# ========== CONFIGURATION ==========
# These values will be automatically filled by the Threatlabs platform
AGENT_ID = $agent_id
AGENT_TOKEN = "$agent_token"
SERVER_URL = "$server_url"
REPORT_ENDPOINT = SERVER_URL + "/api/agent/report"
SSH_PORT = $ssh_port
SSH_BANNER = "$ssh_banner"


# Honeypot Configuration
SSH_HOST = "0.0.0.0"
REPORT_INTERVAL = 30  # seconds

# ===================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Storage for collected attacks
collected_attacks = []
attacks_lock = threading.Lock()

HOST_KEY = None

class SSHServerHandler(paramiko.ServerInterface):
    """Handles SSH authentication attempts"""

    def __init__(self, client_address):
        self.client_address = client_address
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        """Capture username/password attempts and always reject"""
        logger.info(f"Auth attempt from {self.client_address[0]}: {username}:{password}")

        # Collect attack data
        attack_data = {
            'source_ip': self.client_address[0],
            'source_port': self.client_address[1],
            'target_port': SSH_PORT,
            'username_attempt': username,
            'password_attempt': password,
            'timestamp': datetime.utcnow().isoformat(),
            'service_type': 'ssh'
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
        time.sleep(REPORT_INTERVAL)

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
                geo_data = get_ip_geolocation(attack['source_ip'])
                attack.update(geo_data)

                # Add agent ID
                attack['agent_id'] = AGENT_ID

                # Send to server
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {AGENT_TOKEN}'
                }

                response = requests.post(
                    REPORT_ENDPOINT,
                    json=attack,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info(f"Successfully reported attack from {attack['source_ip']}")
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


def handle_client(client_socket, client_address):
    """Handle individual SSH client connections"""
    try:
        # Create SSH transport
        transport = paramiko.Transport(client_socket)

        # Use the global host key
        transport.add_server_key(HOST_KEY)

        # Set custom SSH banner
        transport.local_version = SSH_BANNER

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


def start_ssh_honeypot():
    """Start the SSH honeypot server"""
    global HOST_KEY

    logger.info(f"Starting SSH Honeypot on {SSH_HOST}:{SSH_PORT}")
    logger.info(f"Agent ID: {AGENT_ID}")
    logger.info(f"Reporting to: {REPORT_ENDPOINT}")

    # Generate host key once
    logger.info("Generating host key...")
    HOST_KEY = paramiko.RSAKey.generate(2048)
    logger.info("Host key generated")

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((SSH_HOST, SSH_PORT))
    except OSError as e:
        logger.error(f"Failed to bind to port {SSH_PORT}: {e}")
        logger.error("Make sure you have permission to bind to this port (use sudo for ports < 1024)")
        sys.exit(1)

    server_socket.listen(100)
    logger.info(f"SSH Honeypot listening on port {SSH_PORT}")

    # Start reporting thread
    reporter_thread = threading.Thread(target=report_attacks, daemon=True)
    reporter_thread.start()

    # Accept connections
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            logger.info(f"Connection from {client_address[0]}:{client_address[1]}")

            # Handle client in separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        logger.info("Shutting down honeypot...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Threatlabs SSH Honeypot Agent")
    logger.info("="*60)


    start_ssh_honeypot()
