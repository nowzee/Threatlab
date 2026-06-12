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
import hashlib
import random
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

# FTP interactive-mode exclusivity: only one interactive bot at a time.
# While held, other bots can only brute-force (530).
ftp_interactive_lock = threading.Lock()


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

def queue_attack(data):
    """Append an event to the send queue (automatic timestamp)."""
    data.setdefault('timestamp', datetime.now().isoformat())
    with attacks_lock:
        collected_attacks.append(data)


class SSHServerHandler(paramiko.ServerInterface):
    """Handles SSH authentication and, in interactive mode, the emulated shell."""

    def __init__(self, client_address):
        self.client_address = client_address
        self.event = threading.Event()
        self.username = None
        self.shell_requested = False
        self.exec_command = None

    def check_auth_password(self, username, password):
        """Capture the user/pass attempt."""
        if config.get('features', {}).get('auth_detection', True):
            logger.info(f"SSH auth attempt from {self.client_address[0]}: {username}:{password}")
            queue_attack({
                'source_ip': self.client_address[0],
                'source_port': self.client_address[1],
                'target_port': config.get('ssh', {}).get('port', 22),
                'username_attempt': username,
                'password_attempt': password,
                'service_type': 'ssh',
                'attack_type': 'auth_attempt',
                'classification': 'auth_attempt',
            })

        # Interactive mode: accept the login to observe post-authentication
        # behavior (commands). Otherwise: always reject.
        if config.get('ssh', {}).get('interactive', False):
            self.username = username
            return paramiko.AUTH_SUCCESSFUL
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

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        self.shell_requested = True
        self.event.set()
        return True

    def check_channel_exec_request(self, channel, command):
        # Non-interactive bot: ssh host "command"
        try:
            self.exec_command = command.decode('utf-8', errors='ignore')
        except Exception:
            self.exec_command = str(command)
        self.event.set()
        return True


def get_ip_geolocation(ip_address):
    """Get geolocation data for an IP address"""
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return {
                'country_name': data.get('country_name'),
                'country_code': data.get('country_code'),
                'city': data.get('city'),
                'region': data.get('region')
            }
    except Exception as e:
        logger.debug(f"Geolocation skipped for {ip_address}: {e}")

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
                    timeout=5,
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


# ========== SHELL EMULATION (interactive mode) ==========

DEFAULT_HOSTNAME = "srv01"

DEFAULT_MOTD = (
    "Welcome to Ubuntu 20.04.3 LTS (GNU/Linux 5.4.0-91-generic x86_64)\n"
    "\n"
    " * Documentation:  https://help.ubuntu.com\n"
    " * Management:     https://landscape.canonical.com\n"
    " * Support:        https://ubuntu.com/advantage\n"
    "\n"
    "Last login: Mon Jan  1 00:00:00 2024 from 10.0.0.2\n"
)


def build_filesystem():
    """Build a fake in-memory filesystem (dirs=dict, files=str)."""
    return {
        'bin': {}, 'sbin': {}, 'lib': {}, 'usr': {'bin': {}, 'local': {'bin': {}}},
        'tmp': {}, 'opt': {},
        'etc': {
            'hostname': DEFAULT_HOSTNAME + "\n",
            'passwd': (
                "root:x:0:0:root:/root:/bin/bash\n"
                "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
                "sshd:x:110:65534::/run/sshd:/usr/sbin/nologin\n"
                "admin:x:1000:1000:admin:/home/admin:/bin/bash\n"
            ),
            'os-release': (
                'NAME="Ubuntu"\nVERSION="20.04.3 LTS (Focal Fossa)"\n'
                'ID=ubuntu\nVERSION_ID="20.04"\n'
            ),
        },
        'root': {'.bashrc': "# ~/.bashrc\n", '.ssh': {}},
        'home': {'admin': {'.bashrc': "# ~/.bashrc\n"}},
        'var': {
            'log': {'auth.log': "", 'syslog': ""},
            'www': {'html': {'index.html': "<html><body>It works!</body></html>\n"}},
        },
    }


class ShellEmulator:
    """Emulates a minimal Linux shell over a fake filesystem."""

    def __init__(self, username, hostname):
        self.user = username or 'root'
        self.host = hostname or DEFAULT_HOSTNAME
        self.fs = build_filesystem()
        if self.user == 'root':
            self.cwd = ['root']
        else:
            # Make sure the user's home exists
            self.fs.setdefault('home', {}).setdefault(self.user, {})
            self.cwd = ['home', self.user]

    def home(self):
        return '/root' if self.user == 'root' else '/home/' + self.user

    def cwd_path(self):
        return '/' + '/'.join(self.cwd)

    def cwd_display(self):
        path = self.cwd_path()
        home = self.home()
        if path == home:
            return '~'
        if path.startswith(home + '/'):
            return '~' + path[len(home):]
        return path

    def prompt(self):
        # root -> '#', otherwise the dollar sign via chr(36) (avoids template substitution)
        symbol = '#' if self.user == 'root' else chr(36)
        return self.user + '@' + self.host + ':' + self.cwd_display() + symbol + ' '

    def _resolve(self, path):
        """Resolve a path to (node, parts); (None, None) if not found."""
        parts = [] if path.startswith('/') else list(self.cwd)
        for seg in path.split('/'):
            if seg in ('', '.'):
                continue
            if seg == '..':
                if parts:
                    parts.pop()
                continue
            parts.append(seg)
        node = self.fs
        for seg in parts:
            if isinstance(node, dict) and seg in node:
                node = node[seg]
            else:
                return None, None
        return node, parts

    def _ls(self, args):
        long_fmt = any(a.startswith('-') and 'l' in a for a in args)
        targets = [a for a in args if not a.startswith('-')]
        path = targets[0] if targets else '.'
        node, _ = self._resolve(path)
        if node is None:
            return "ls: cannot access '" + path + "': No such file or directory\n"
        if not isinstance(node, dict):
            return path + "\n"
        names = sorted(node.keys())
        if not names:
            return ""
        if long_fmt:
            lines = ["total " + str(len(names) * 4)]
            for n in names:
                is_dir = isinstance(node[n], dict)
                perm = 'drwxr-xr-x' if is_dir else '-rw-r--r--'
                size = 4096 if is_dir else len(node[n])
                lines.append(perm + " 1 " + self.user + " " + self.user +
                             " " + str(size).rjust(6) + " Jan  1 00:00 " + n)
            return '\n'.join(lines) + '\n'
        return '  '.join(names) + '\n'

    def _cd(self, args):
        path = args[0] if args else self.home()
        if path == '~':
            path = self.home()
        node, parts = self._resolve(path)
        if node is None:
            return "bash: cd: " + path + ": No such file or directory\n"
        if not isinstance(node, dict):
            return "bash: cd: " + path + ": Not a directory\n"
        self.cwd = parts
        return ""

    def _cat(self, args):
        if not args:
            return ""
        out = []
        for path in args:
            node, _ = self._resolve(path)
            if node is None:
                out.append("cat: " + path + ": No such file or directory")
            elif isinstance(node, dict):
                out.append("cat: " + path + ": Is a directory")
            else:
                out.append(node.rstrip('\n'))
        return '\n'.join(out) + '\n'

    def execute(self, line):
        """Execute a command line. Returns (output, should_exit)."""
        parts = line.strip().split()
        if not parts:
            return "", False
        cmd, args = parts[0], parts[1:]

        if cmd in ('exit', 'logout'):
            return "", True
        if cmd == 'whoami':
            return self.user + "\n", False
        if cmd == 'id':
            if self.user == 'root':
                return "uid=0(root) gid=0(root) groups=0(root)\n", False
            return ("uid=1000(" + self.user + ") gid=1000(" + self.user +
                    ") groups=1000(" + self.user + ")\n"), False
        if cmd == 'pwd':
            return self.cwd_path() + "\n", False
        if cmd == 'uname':
            if '-a' in args:
                return ("Linux " + self.host + " 5.4.0-91-generic #102-Ubuntu SMP "
                        "Fri Nov 5 16:31:28 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux\n"), False
            return "Linux\n", False
        if cmd == 'hostname':
            return self.host + "\n", False
        if cmd == 'ls':
            return self._ls(args), False
        if cmd == 'cd':
            return self._cd(args), False
        if cmd == 'cat':
            return self._cat(args), False
        if cmd == 'echo':
            return ' '.join(args) + "\n", False
        if cmd == 'ps':
            return ("  PID TTY          TIME CMD\n"
                    "    1 ?        00:00:01 systemd\n"
                    "  912 ?        00:00:00 sshd\n"
                    " 1337 pts/0    00:00:00 bash\n"
                    " 1340 pts/0    00:00:00 ps\n"), False
        if cmd == 'uptime':
            return (" 00:00:00 up 10 days,  3:14,  1 user,  "
                    "load average: 0.00, 0.01, 0.05\n"), False
        if cmd == 'clear':
            return "\x1b[H\x1b[2J", False
        if cmd == 'help':
            return "GNU bash, version 5.0.17(1)-release\n", False
        if cmd in ('wget', 'curl'):
            # "Silent" download: logged separately by log_command.
            return "", False
        if cmd in ('mkdir', 'touch', 'rm', 'chmod', 'chown', 'export', 'kill', 'killall'):
            return "", False  # silently accepted
        return cmd + ": command not found\n", False


def log_command(command, handler):
    """Log and queue an observed shell command."""
    logger.info("SSH command from " + handler.client_address[0] + ": " + command)
    base = {
        'source_ip': handler.client_address[0],
        'source_port': handler.client_address[1],
        'target_port': config.get('ssh', {}).get('port', 22),
        'username_attempt': handler.username,
        'service_type': 'ssh',
    }
    queue_attack(dict(base, attack_type='shell_command',
                      classification='shell_command', payload=command))

    low = command.strip().lower()
    if low.startswith('wget ') or low.startswith('curl '):
        urls = [t for t in command.split()
                if t.startswith('http://') or t.startswith('https://') or t.startswith('ftp://')]
        queue_attack(dict(base, attack_type='malware_download',
                          classification='malware_download',
                          payload=' '.join(urls) if urls else command))


def run_shell_session(channel, handler):
    """Interactive shell loop: reads keystrokes, emulates, returns output."""
    emu = ShellEmulator(handler.username, config.get('ssh', {}).get('hostname', DEFAULT_HOSTNAME))

    motd = config.get('ssh', {}).get('motd', DEFAULT_MOTD)
    if motd:
        channel.send(motd.replace('\n', '\r\n'))
    channel.send(emu.prompt())

    line = ''
    while True:
        try:
            data = channel.recv(1024)
        except Exception:
            break
        if not data:
            break

        for byte in data:
            if byte in (13, 10):  # CR / LF
                channel.send('\r\n')
                cmd = line.strip()
                line = ''
                if cmd:
                    log_command(cmd, handler)
                    output, should_exit = emu.execute(cmd)
                    if should_exit:
                        channel.send('logout\r\n')
                        return
                    if output:
                        channel.send(output.replace('\n', '\r\n'))
                channel.send(emu.prompt())
            elif byte in (127, 8):  # backspace
                if line:
                    line = line[:-1]
                    channel.send('\b \b')
            elif byte == 3:  # Ctrl-C
                channel.send('^C\r\n')
                line = ''
                channel.send(emu.prompt())
            elif byte == 4:  # Ctrl-D
                if not line:
                    channel.send('logout\r\n')
                    return
            elif 32 <= byte < 127:  # printable character -> echo
                line += chr(byte)
                channel.send(chr(byte))


def handle_client_ssh(client_socket, client_address):
    """Handle individual SSH client connections"""
    try:
        # Set socket timeout to prevent hanging connections
        client_socket.settimeout(30)

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

        # Wait for a channel (only opens if auth succeeded, i.e. interactive mode)
        channel = transport.accept(20)
        if channel is None:
            return

        try:
            # Let the client request a shell or run a command
            server_handler.event.wait(10)

            if server_handler.exec_command is not None:
                # Non-interactive bot: a single command then close
                cmd = server_handler.exec_command
                log_command(cmd, server_handler)
                emu = ShellEmulator(server_handler.username,
                                    config.get('ssh', {}).get('hostname', DEFAULT_HOSTNAME))
                output, _ = emu.execute(cmd)
                if output:
                    channel.send(output.replace('\n', '\r\n'))
                try:
                    channel.send_exit_status(0)
                except Exception:
                    pass
            elif server_handler.shell_requested:
                run_shell_session(channel, server_handler)
        finally:
            try:
                channel.close()
            except Exception:
                pass

    except paramiko.SSHException as e:
        logger.debug(f"SSH negotiation failed with {client_address[0]}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_address[0]}: {e}")
    finally:
        try:
            transport.close()
        except:
            pass


def _ftp_open_data_connection(state, timeout=20):
    """Open the FTP data connection (PASV: accept; PORT: connect). None on failure."""
    if state.get('pasv_listener') is not None:
        lst = state['pasv_listener']
        try:
            lst.settimeout(timeout)
            data_conn, _ = lst.accept()
            return data_conn
        except Exception:
            return None
        finally:
            try:
                lst.close()
            except Exception:
                pass
            state['pasv_listener'] = None
    if state.get('active_addr') is not None:
        try:
            return socket.create_connection(state['active_addr'], timeout=timeout)
        except Exception:
            return None
    return None


def send_file_to_server(file_bytes, filename, meta):
    """Send the uploaded binary to the server (server-side dedup by hash)."""
    try:
        url = config.get('server_url', '') + '/api/agent/upload'
        headers = {'Authorization': f'Bearer {config.get("agent_token", "")}'}
        r = requests.post(
            url,
            files={'file': (filename or 'upload.bin', file_bytes)},
            data=meta,
            headers=headers,
            timeout=30,
            verify=False,
        )
        if r.status_code == 200:
            logger.info(f"Upload sent to server: {meta.get('file_hash')} ({len(file_bytes)} bytes)")
            return True
        logger.error(f"Upload rejected by server: HTTP {r.status_code} {r.text[:200]}")
    except Exception as e:
        logger.error(f"Could not send file to server: {e}")
    return False


def _process_ftp_upload(file_bytes, filename, username, password, addr, ftp_port, cmd_log):
    """Compute the hash, log the upload and forward the file to the server."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    logger.info(f"FTP upload from {addr[0]}: {filename} ({len(file_bytes)} bytes) sha256={file_hash}")

    queue_attack({
        'source_ip': addr[0], 'source_port': addr[1], 'target_port': ftp_port,
        'username_attempt': username or "", 'password_attempt': password or "",
        'service_type': 'ftp', 'attack_type': 'file_upload', 'classification': 'file_upload',
        'malware_hash': file_hash, 'payload': filename,
    })

    send_file_to_server(file_bytes, filename, {
        'file_hash': file_hash,
        'file_name': filename or 'upload.bin',
        'file_size': str(len(file_bytes)),
        'source_ip': addr[0],
        'username': username or "",
        'password': password or "",
        'request_headers': "\n".join(cmd_log)[:8000],
        'agent_id': str(config.get('agent_id', 1)),
        'service_type': 'ftp',
    })


def handle_client_ftp(conn, addr):
    """
    FTP honeypot: credential capture (always) + exclusive interactive mode.

    The first bot that authenticates gets an interactive session (uploads
    allowed) for 10 to 15 min; while it lasts, other bots can only brute-force
    (530). Uploaded files are hashed and sent to the server with ip, credentials
    and the command transcript.
    """
    peer = f"{addr[0]}:{addr[1]}"
    ftp_cfg = config.get('ftp', {})
    ftp_port = ftp_cfg.get('port', 21)
    interactive_enabled = ftp_cfg.get('interactive', False)
    smin = int(ftp_cfg.get('session_min_seconds', 600))
    smax = int(ftp_cfg.get('session_max_seconds', 900))
    max_size = int(ftp_cfg.get('max_upload_bytes', 50 * 1024 * 1024))

    try:
        local_ip = conn.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    pasv_ip = ftp_cfg.get('public_ip') or local_ip

    state = {'pasv_listener': None, 'active_addr': None}
    username = None
    password = None
    authenticated = False   # interactive session granted
    holds_slot = False      # this thread holds the interactive lock
    deadline = None
    cmd_log = []
    done = False

    def send(text):
        conn.sendall(text.encode())

    def open_pasv(extended):
        if state['pasv_listener'] is not None:
            try:
                state['pasv_listener'].close()
            except Exception:
                pass
        lst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lst.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lst.bind(('0.0.0.0', 0))
        lst.listen(1)
        state['pasv_listener'] = lst
        port = lst.getsockname()[1]
        if extended:
            send("229 Entering Extended Passive Mode (|||%d|)\r\n" % port)
        else:
            h = pasv_ip.split('.')
            if len(h) != 4:
                h = ['127', '0', '0', '1']
            send("227 Entering Passive Mode (%s,%s,%s,%s,%d,%d).\r\n"
                 % (h[0], h[1], h[2], h[3], port // 256, port % 256))

    def need_login():
        send("530 Please login with USER and PASS.\r\n")

    try:
        send(ftp_cfg.get('banner', '220 FTP server ready') + "\r\n")
        buf = b""
        conn.settimeout(30)

        while not done:
            if deadline is not None and time.time() > deadline:
                send("421 Session timeout, closing control connection.\r\n")
                break
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
                arg = parts[1].strip() if len(parts) > 1 else ""
                cmd_log.append(cmd + (" ******" if cmd == "PASS" else ((" " + arg) if arg else "")))

                if cmd == "USER":
                    username = arg
                    send("331 Please specify the password.\r\n")

                elif cmd == "PASS":
                    password = arg
                    # Always capture the credential attempt.
                    if config.get('features', {}).get('auth_detection', True):
                        logger.info(f"FTP auth attempt from {addr[0]}: {username}:{password}")
                        queue_attack({
                            'source_ip': addr[0], 'source_port': addr[1], 'target_port': ftp_port,
                            'username_attempt': username or "", 'password_attempt': password or "",
                            'service_type': 'ftp', 'attack_type': 'auth_attempt',
                            'classification': 'auth_attempt',
                        })
                    # Interactive mode: granted to a single bot at a time.
                    if interactive_enabled and not authenticated and ftp_interactive_lock.acquire(blocking=False):
                        authenticated = True
                        holds_slot = True
                        deadline = time.time() + random.randint(smin, smax)
                        logger.info(f"FTP interactive session granted to {addr[0]}")
                        send("230 Login successful.\r\n")
                    else:
                        send("530 Login incorrect.\r\n")

                elif cmd == "SYST":
                    send("215 UNIX Type: L8\r\n")
                elif cmd == "FEAT":
                    send("211-Features:\r\n PASV\r\n EPSV\r\n UTF8\r\n SIZE\r\n211 End\r\n")
                elif cmd == "OPTS":
                    send("200 OK\r\n")
                elif cmd == "NOOP":
                    send("200 NOOP ok.\r\n")
                elif cmd == "TYPE":
                    send("200 Switching to Binary mode.\r\n")
                elif cmd in ("PWD", "XPWD"):
                    send("257 \"/\" is the current directory\r\n")
                elif cmd in ("CWD", "CDUP", "XCUP"):
                    if authenticated:
                        send("250 Directory successfully changed.\r\n")
                    else:
                        need_login()
                elif cmd in ("MKD", "XMKD"):
                    if authenticated:
                        send("257 \"%s\" created\r\n" % arg)
                    else:
                        need_login()
                elif cmd == "PASV":
                    if authenticated:
                        open_pasv(False)
                    else:
                        need_login()
                elif cmd == "EPSV":
                    if authenticated:
                        open_pasv(True)
                    else:
                        need_login()
                elif cmd == "PORT":
                    if not authenticated:
                        need_login()
                    else:
                        try:
                            nums = [int(x) for x in arg.split(",")]
                            state['active_addr'] = (".".join(str(n) for n in nums[:4]), nums[4] * 256 + nums[5])
                            send("200 PORT command successful.\r\n")
                        except Exception:
                            send("501 Syntax error in parameters.\r\n")
                elif cmd in ("STOR", "STOU", "APPE"):
                    if not authenticated:
                        need_login()
                    else:
                        filename = arg or "upload.bin"
                        send("150 Ok to send data.\r\n")
                        data_conn = _ftp_open_data_connection(state)
                        if data_conn is None:
                            send("425 Can't open data connection.\r\n")
                        else:
                            file_bytes = b""
                            try:
                                data_conn.settimeout(30)
                                while True:
                                    chunk = data_conn.recv(65536)
                                    if not chunk:
                                        break
                                    file_bytes += chunk
                                    if len(file_bytes) > max_size:
                                        logger.warning(f"FTP upload tronqué (>{max_size} o) de {addr[0]}")
                                        break
                            except Exception:
                                pass
                            finally:
                                try:
                                    data_conn.close()
                                except Exception:
                                    pass
                            send("226 Transfer complete.\r\n")
                            try:
                                _process_ftp_upload(file_bytes, filename, username, password, addr, ftp_port, cmd_log)
                            except Exception as e:
                                logger.error(f"Erreur traitement upload: {e}")
                elif cmd in ("LIST", "NLST"):
                    if not authenticated:
                        need_login()
                    else:
                        send("150 Here comes the directory listing.\r\n")
                        data_conn = _ftp_open_data_connection(state)
                        if data_conn is None:
                            send("425 Can't open data connection.\r\n")
                        else:
                            try:
                                data_conn.sendall(
                                    b"drwxr-xr-x 2 0 0 4096 Jan 01 00:00 .\r\n"
                                    b"drwxr-xr-x 2 0 0 4096 Jan 01 00:00 ..\r\n")
                            except Exception:
                                pass
                            finally:
                                try:
                                    data_conn.close()
                                except Exception:
                                    pass
                            send("226 Directory send OK.\r\n")
                elif cmd == "QUIT":
                    send("221 Goodbye.\r\n")
                    done = True
                    break
                else:
                    if authenticated:
                        send("502 Command not implemented.\r\n")
                    else:
                        need_login()

    except socket.timeout:
        pass
    except Exception as e:
        logger.error(f"Error handling FTP client {peer}: {e}")
    finally:
        if state.get('pasv_listener') is not None:
            try:
                state['pasv_listener'].close()
            except Exception:
                pass
        if holds_slot:
            try:
                ftp_interactive_lock.release()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
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
