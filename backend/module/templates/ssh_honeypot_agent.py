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
import re
import hashlib
import random
from datetime import datetime
import logging
import json
from collections import defaultdict

# ========== CONFIGURATION ==========
CONFIG_FILE = "honeypot_config.json"

# Default configuration (injected by server as JSON, parsed safely at import).
DEFAULT_CONFIG = json.loads(r"""$default_config_json""")

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


def _auth_allowed(username, password):
    auth_cfg = config.get('auth', {}) if isinstance(config, dict) else {}
    mode = str(auth_cfg.get('mode') or 'any').lower()
    allow = auth_cfg.get('allow') or []
    if mode != 'whitelist' or not allow:
        return True
    for entry in allow:
        if not isinstance(entry, dict):
            continue
        u = entry.get('username')
        p = entry.get('password')
        has_u = u not in (None, '')
        has_p = p not in (None, '')
        if not has_u and not has_p:
            continue  # empty entry -> ignore
        if (not has_u or u == username) and (not has_p or p == password):
            return True
    return False


def _in_container():
    """True if running inside a Docker/OCI container. Inside a container the
    host's configured IP isn't bindable, so we listen on 0.0.0.0 instead."""
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            data = f.read()
        return ('docker' in data) or ('containerd' in data) or ('kubepods' in data)
    except Exception:
        return False


def _service_ports(service, default_port):
    """Ports the given service should listen on: config['<svc>']['ports'] (list),
    falling back to config['<svc>']['port'], then default. De-duped int list."""
    cfg = config.get(service, {}) if isinstance(config, dict) else {}
    out = []
    raw = cfg.get('ports')
    if isinstance(raw, list):
        for p in raw:
            try:
                pi = int(p)
            except (TypeError, ValueError):
                continue
            if 1 <= pi <= 65535 and pi not in out:
                out.append(pi)
    if out:
        return out
    try:
        return [int(cfg.get('port', default_port))]
    except (TypeError, ValueError):
        return [default_port]


class SSHServerHandler(paramiko.ServerInterface):
    """Handles SSH authentication and, in interactive mode, the emulated shell."""

    def __init__(self, client_address, local_port=None):
        self.client_address = client_address
        self.local_port = local_port if local_port else config.get('ssh', {}).get('port', 22)
        self.event = threading.Event()
        self.username = None
        self.password = None
        self.shell_requested = False
        self.exec_command = None
        self.sftp_requested = False

    def check_auth_password(self, username, password):
        """Always capture the user/pass attempt, then grant the shell per policy."""
        # Credential capture is ALWAYS on (never disabled, even in interactive mode).
        logger.info(f"SSH auth attempt from {self.client_address[0]}: {username}:{password}")
        queue_attack({
            'source_ip': self.client_address[0],
            'source_port': self.client_address[1],
            'target_port': self.local_port,
            'username_attempt': username,
            'password_attempt': password,
            'service_type': 'ssh',
            'attack_type': 'auth_attempt',
            'classification': 'auth_attempt',
        })

        # Only interactive mode grants an emulated shell (to observe commands /
        # SFTP uploads), and only for credentials allowed by the whitelist.
        if config.get('ssh', {}).get('interactive', False) and _auth_allowed(username, password):
            self.username = username
            self.password = password
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

    def check_channel_subsystem_request(self, channel, name):
        # SFTP file upload (sftp subsystem over SSH).
        if name == 'sftp':
            self.sftp_requested = True
            self.event.set()
        return super().check_channel_subsystem_request(channel, name)


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
    bin_files = {name: "" for name in (
        'busybox', 'sh', 'bash', 'cat', 'ls', 'echo', 'wget', 'curl', 'chmod',
        'cp', 'rm', 'mv', 'ps', 'kill', 'mount', 'dd', 'tftp', 'nc', 'ssh', 'scp')}
    return {
        'bin': dict(bin_files), 'sbin': {}, 'lib': {}, 'usr': {'bin': dict(bin_files), 'local': {'bin': {}}},
        'tmp': {}, 'opt': {}, 'mnt': {}, 'run': {},
        'dev': {'null': "", 'zero': "", 'urandom': "", 'shm': {}},
        'etc': {
            'hostname': DEFAULT_HOSTNAME + "\n",
            'passwd': (
                "root:x:0:0:root:/root:/bin/bash\n"
                "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
                "sshd:x:110:65534::/run/sshd:/usr/sbin/nologin\n"
                "admin:x:1000:1000:admin:/home/admin:/bin/bash\n"
            ),
            'hosts': "127.0.0.1\tlocalhost\n127.0.1.1\t" + DEFAULT_HOSTNAME + "\n",
            'issue': "Ubuntu 20.04.3 LTS \\n \\l\n",
            'os-release': (
                'NAME="Ubuntu"\nVERSION="20.04.3 LTS (Focal Fossa)"\n'
                'ID=ubuntu\nID_LIKE=debian\nVERSION_ID="20.04"\n'
            ),
        },
        'proc': {
            'cpuinfo': (
                "processor\t: 0\nvendor_id\t: GenuineIntel\ncpu family\t: 6\n"
                "model name\t: Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz\ncpu MHz\t\t: 2599.998\n"
                "cache size\t: 20480 KB\nflags\t\t: fpu vme de pse tsc msr\n\n"
                "processor\t: 1\nvendor_id\t: GenuineIntel\ncpu family\t: 6\n"
                "model name\t: Intel(R) Xeon(R) CPU E5-2670 0 @ 2.60GHz\ncpu MHz\t\t: 2599.998\n"
            ),
            'meminfo': (
                "MemTotal:        2041000 kB\nMemFree:         1502344 kB\n"
                "MemAvailable:    1723016 kB\nBuffers:           58112 kB\nCached:           312456 kB\n"
                "SwapTotal:        998396 kB\nSwapFree:         998396 kB\n"
            ),
            'mounts': (
                "sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0\n"
                "proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0\n"
                "/dev/sda1 / ext4 rw,relatime 0 0\n"
                "tmpfs /run tmpfs rw,nosuid,nodev 0 0\n"
            ),
            'version': (
                "Linux version 5.4.0-91-generic (buildd@lcy01) "
                "(gcc 9.3.0) #102-Ubuntu SMP Fri Nov 5 16:31:28 UTC 2021\n"
            ),
            'filesystems': "nodev\tsysfs\nnodev\tproc\n\text4\n\tvfat\n",
        },
        'root': {'.bashrc': "# ~/.bashrc\n", '.ssh': {}},
        'home': {'admin': {'.bashrc': "# ~/.bashrc\n"}},
        'var': {
            'log': {'auth.log': "", 'syslog': ""},
            'www': {'html': {'index.html': "<html><body>It works!</body></html>\n"}},
            'run': {},
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

    # Commands accepted silently (recognized, no realistic output needed).
    _NOOP = frozenset((
        'mkdir', 'touch', 'rm', 'chmod', 'chown', 'export', 'unset', 'set',
        'kill', 'killall', 'cp', 'mv', 'dd', 'ln', 'sync', 'sleep', 'sysctl',
        'iptables', 'service', 'systemctl', 'insmod', 'rmmod', 'modprobe',
        'umask', 'alias', 'unalias', 'true', 'false', ':', 'wait',
        'tftp', 'ftpget', 'nc', 'ncat', 'setsid', 'nohup', 'pkill',
        # text / shell utilities frequently used by bots
        'grep', 'egrep', 'fgrep', 'sed', 'awk', 'cut', 'sort', 'uniq', 'wc',
        'tr', 'xargs', 'tee', 'read', 'test', 'expr', 'eval', 'source', '.',
        'sleep', 'usleep', 'timeout', 'flock', 'mktemp', 'basename', 'dirname',
        # interpreters / build / archive (payload execution)
        'perl', 'python', 'python3', 'python2', 'php', 'ruby', 'lua', 'node',
        'gcc', 'cc', 'g++', 'make', 'ld', 'strip', 'tar', 'gzip', 'gunzip',
        'bzip2', 'unzip', 'zip', 'xz', 'base64', 'openssl', 'gpg',
        # hashing / inspection
        'md5sum', 'sha1sum', 'sha256sum', 'cksum', 'strings', 'file', 'stat',
        'readlink', 'realpath', 'lsattr', 'chattr', 'getconf', 'ldconfig', 'ldd',
        # process / network / system probes
        'top', 'htop', 'netstat', 'ss', 'ifconfig', 'ip', 'route', 'arp',
        'iptables-save', 'last', 'lastlog', 'w', 'who', 'users', 'groups',
        'lscpu', 'lsblk', 'lsof', 'lsmod', 'dmesg', 'mount', 'umount',
        'useradd', 'userdel', 'usermod', 'passwd', 'su', 'sudo', 'login',
        'screen', 'tmux', 'at', 'batch', 'logger', 'reboot', 'shutdown',
        'halt', 'poweroff', 'wall', 'write', 'mesg', 'reset', 'tput'))

    # Busybox applets we "know" (anything else -> "applet not found").
    _BUSYBOX = frozenset((
        'cat', 'ls', 'echo', 'pwd', 'whoami', 'id', 'uname', 'ps', 'wget',
        'cp', 'rm', 'mv', 'chmod', 'kill', 'sh', 'mount', 'dd', 'cd', 'free',
        'df', 'head', 'tail', 'grep', 'which', 'hostname', 'sleep', 'tftp'))

    def execute(self, line):
        """Execute a possibly-chained command line. Returns (output, should_exit)."""
        out = []
        for stmt in re.split(r'\s*(?:&&|\|\||;|\n)\s*', line.strip()):
            if not stmt.strip():
                continue
            # Emulate pipes by running only the left-most command.
            stmt = stmt.split('|', 1)[0]
            text, should_exit = self._run_one(stmt)
            if text:
                out.append(text)
            if should_exit:
                return ''.join(out), True
        return ''.join(out), False

    def _run_one(self, stmt):
        # Drop simple output redirections (> f, >> f, 2> f, 2>&1).
        stmt = stmt.replace('2>&1', '')
        stmt = re.sub(r'\s*\d?>>?\s*\S+', '', stmt).strip()
        toks = stmt.split()
        if not toks:
            return "", False
        cmd, args = toks[0], toks[1:]
        # A path-based invocation (./x, /tmp/x, ../x) is a dropped binary.
        was_path = cmd.startswith('/') or cmd.startswith('./') or cmd.startswith('../')
        # Normalize absolute/relative paths: /bin/busybox -> busybox, ./x -> x
        if '/' in cmd:
            cmd = cmd.rsplit('/', 1)[1]
        out, should_exit = self._dispatch(cmd, args)
        # Fake execution: a dropped binary "runs" silently instead of erroring.
        if was_path and out.endswith('command not found\n'):
            return "", False
        return out, should_exit

    def _dispatch(self, cmd, args):
        if cmd in ('exit', 'logout', 'quit'):
            return "", True
        if cmd == 'busybox':
            return self._busybox(args)
        if cmd == 'echo':
            return self._echo(args)
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
            return self._uname(args)
        if cmd == 'hostname':
            return self.host + "\n", False
        if cmd == 'ls':
            return self._ls(args), False
        if cmd == 'cd':
            return self._cd(args), False
        if cmd == 'cat':
            return self._cat(args), False
        if cmd == 'head' or cmd == 'tail':
            return self._cat([a for a in args if not a.startswith('-')][:1] or args), False
        if cmd == 'ps':
            return ("  PID TTY          TIME CMD\n"
                    "    1 ?        00:00:01 systemd\n"
                    "  912 ?        00:00:00 sshd\n"
                    " 1337 pts/0    00:00:00 bash\n"
                    " 1340 pts/0    00:00:00 ps\n"), False
        if cmd == 'uptime':
            return (" 00:00:00 up 10 days,  3:14,  1 user,  "
                    "load average: 0.00, 0.01, 0.05\n"), False
        if cmd == 'nproc':
            return "2\n", False
        if cmd == 'free':
            return ("              total        used        free      shared  buff/cache   available\n"
                    "Mem:        2041000      210000     1502344        1024      328656     1723016\n"
                    "Swap:        998396           0      998396\n"), False
        if cmd == 'df':
            return ("Filesystem     1K-blocks    Used Available Use% Mounted on\n"
                    "/dev/sda1       41152812 6230112  32800316  16% /\n"
                    "tmpfs            1020500       0   1020500   0% /run\n"), False
        if cmd == 'which':
            if args and args[0] in self._BUSYBOX or (args and args[0] in self._NOOP):
                return "/bin/" + args[0] + "\n", False
            return "", False
        if cmd == 'crontab':
            return "no crontab for " + self.user + "\n", False
        if cmd == 'history':
            return "", False
        if cmd in ('env', 'printenv'):
            return self._env(), False
        if cmd == 'printf':
            return self._printf(args), False
        if cmd == 'date':
            return "Mon Jan  1 00:00:00 UTC 2024\n", False
        if cmd == 'clear':
            return "\x1b[H\x1b[2J", False
        if cmd == 'help':
            return "GNU bash, version 5.0.17(1)-release\n", False
        if cmd in ('wget', 'curl'):
            return "", False  # "silent" download: logged by log_command
        if cmd in ('sh', 'bash', 'enable', 'system', 'shell'):
            return "", False  # subshell / router prompts: no-op
        if cmd in self._NOOP:
            return "", False
        return cmd + ": command not found\n", False

    def _uname(self, args):
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        if 'a' in flags:
            return ("Linux " + self.host + " 5.4.0-91-generic #102-Ubuntu SMP "
                    "Fri Nov 5 16:31:28 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux\n"), False
        if not flags:
            return "Linux\n", False
        # uname prints fields in a fixed order regardless of flag order.
        out = []
        if 's' in flags:
            out.append("Linux")
        if 'n' in flags:
            out.append(self.host)
        if 'r' in flags:
            out.append("5.4.0-91-generic")
        if 'v' in flags:
            out.append("#102-Ubuntu SMP Fri Nov 5 16:31:28 UTC 2021")
        if 'm' in flags:
            out.append("x86_64")
        if 'p' in flags:
            out.append("x86_64")
        if 'i' in flags:
            out.append("x86_64")
        if 'o' in flags:
            out.append("GNU/Linux")
        return (' '.join(out) if out else "Linux") + "\n", False

    def _echo(self, args):
        newline = True
        interpret = False
        i = 0
        while i < len(args) and args[i].startswith('-') and set(args[i][1:]) <= set('neE'):
            if 'n' in args[i]:
                newline = False
            if 'e' in args[i]:
                interpret = True
            i += 1
        text = ' '.join(args[i:]).strip('"').strip("'")
        if interpret:
            try:
                text = text.encode('latin-1', 'ignore').decode('unicode_escape', 'ignore')
            except Exception:
                pass
        return text + ("\n" if newline else ""), False

    def _env(self):
        return ("SHELL=/bin/bash\nHOME=" + self.home() + "\nUSER=" + self.user +
                "\nLOGNAME=" + self.user +
                "\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
                "PWD=" + self.cwd_path() + "\nHOSTNAME=" + self.host +
                "\nLANG=en_US.UTF-8\nTERM=xterm\nSHLVL=1\n_=/usr/bin/env\n")

    def _printf(self, args):
        if not args:
            return ""
        fmt = ' '.join(args).strip('"').strip("'")
        try:
            fmt = fmt.encode('latin-1', 'ignore').decode('unicode_escape', 'ignore')
        except Exception:
            pass
        return fmt

    def _busybox(self, args):
        if not args:
            return ("BusyBox v1.30.1 (Ubuntu 1:1.30.1-4ubuntu) multi-call binary.\n"
                    "Usage: busybox [function [arguments]...]\n"), False
        applet = args[0]
        if applet in self._BUSYBOX or applet in self._NOOP:
            return self._dispatch(applet, args[1:])
        # Honeypot-detection trick: bots send a random applet and expect this.
        return applet + ": applet not found\n", False


def command_succeeded(output):
    """A command is "failed" if the emulator did not recognize it."""
    return 'command not found' not in output and 'applet not found' not in output


def log_command(command, handler, success=True):
    """Log and queue an observed shell command (success marks a recognized command)."""
    logger.info("SSH command from " + handler.client_address[0] + ": " + command)
    kind = 'shell_command' if success else 'shell_command_failed'
    base = {
        'source_ip': handler.client_address[0],
        'source_port': handler.client_address[1],
        'target_port': config.get('ssh', {}).get('port', 22),
        'username_attempt': handler.username,
        'service_type': 'ssh',
    }
    queue_attack(dict(base, attack_type=kind, classification=kind, payload=command))

    low = command.strip().lower()
    if low.startswith('wget ') or low.startswith('curl '):
        urls = [t for t in command.split()
                if t.startswith('http://') or t.startswith('https://') or t.startswith('ftp://')]
        queue_attack(dict(base, attack_type='malware_download',
                          classification='malware_download',
                          payload=' '.join(urls) if urls else command))

    # Fake execution: actually fetch any download URL and ship the payload.
    if '://' in command:
        fetch_downloads_from_text(command, handler.username, handler.password,
                                  handler.client_address[0], handler.client_address[1])


def _finalize_pasted_script(lines, handler):
    """Store a pasted shell script (detected by shebang) as an uploaded payload."""
    text = '\n'.join(lines) + '\n'
    content = text.encode('utf-8', 'ignore')
    logger.info("Captured pasted script (%d bytes) from %s"
                % (len(content), handler.client_address[0]))
    try:
        process_uploaded_binary(
            content, 'pasted_script.sh', handler.username, handler.password,
            handler.client_address[0], handler.client_address[1],
            config.get('ssh', {}).get('port', 22), 'ssh', 'pasted shell script (shebang)')
    except Exception as e:
        logger.error("Script capture processing error: " + str(e))
    # Fetch any payloads the script downloads (fake execution).
    fetch_downloads_from_text(text, handler.username, handler.password,
                              handler.client_address[0], handler.client_address[1])


def run_shell_session(channel, handler):
    """Interactive shell loop: reads keystrokes, emulates, returns output."""
    emu = ShellEmulator(handler.username, config.get('ssh', {}).get('hostname', DEFAULT_HOSTNAME))
    upload_allowed = config.get('ssh', {}).get('allow_upload', True)

    motd = config.get('ssh', {}).get('motd', DEFAULT_MOTD)
    if motd:
        channel.send(motd.replace('\n', '\r\n'))
    channel.send(emu.prompt())

    line = ''
    script_lines = None  # None = normal mode; list = capturing a pasted script
    while True:
        try:
            data = channel.recv(1024)
        except socket.timeout:
            # Idle while capturing a pasted script -> store it as a payload.
            if script_lines is not None:
                _finalize_pasted_script(script_lines, handler)
                script_lines = None
                channel.settimeout(None)
                channel.send(emu.prompt())
            continue
        except Exception:
            break
        if not data:
            break

        for byte in data:
            if byte in (13, 10):  # CR / LF
                channel.send('\r\n')
                raw = line
                line = ''
                cmd = raw.strip()
                # A line starting with a shebang means a script is being pasted:
                # capture it (and the following lines) as a file, not a command.
                if script_lines is None and upload_allowed and cmd.startswith('#!'):
                    script_lines = [raw]
                    channel.settimeout(1.5)
                    continue
                if script_lines is not None:
                    script_lines.append(raw)
                    continue
                if cmd:
                    output, should_exit = emu.execute(cmd)
                    log_command(cmd, handler, command_succeeded(output))
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


class _SFTPUploadHandle(paramiko.SFTPHandle):
    """Captures the bytes written to a file uploaded over SFTP."""

    def __init__(self, flags, filename, sftp_iface):
        super().__init__(flags)
        self.filename = filename
        self.sftp = sftp_iface
        self.buffer = bytearray()
        self.truncated = False

    def write(self, offset, data):
        if not self.truncated:
            self.buffer.extend(data)
            if len(self.buffer) > self.sftp.max_upload:
                self.truncated = True
                logger.warning("SFTP upload truncated (>%d bytes)" % self.sftp.max_upload)
        return paramiko.SFTP_OK

    def close(self):
        try:
            if self.buffer:
                h = self.sftp.handler
                process_uploaded_binary(
                    bytes(self.buffer[:self.sftp.max_upload]), self.filename,
                    h.username, h.password,
                    h.client_address[0], h.client_address[1],
                    config.get('ssh', {}).get('port', 22),
                    'ssh', 'SFTP put ' + str(self.filename),
                )
        except Exception as e:
            logger.error("SFTP upload processing error: " + str(e))
        return paramiko.SFTP_OK


class HoneypotSFTPServer(paramiko.SFTPServerInterface):
    """Minimal SFTP server: captures uploads, fakes everything else."""

    def __init__(self, server, *largs, **kwargs):
        super().__init__(server, *largs, **kwargs)
        self.handler = server  # SSHServerHandler instance
        self.max_upload = int(config.get('ssh', {}).get('max_upload_bytes', 50 * 1024 * 1024))

    def open(self, path, flags, attr):
        writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND))
        if writing:
            logger.info("SFTP upload start from %s: %s" % (self.handler.client_address[0], path))
            return _SFTPUploadHandle(flags, path, self)
        # Reads: nothing real to serve.
        return paramiko.SFTP_PERMISSION_DENIED

    def list_folder(self, path):
        return []

    def stat(self, path):
        return paramiko.SFTP_NO_SUCH_FILE

    def lstat(self, path):
        return paramiko.SFTP_NO_SUCH_FILE

    def remove(self, path):
        return paramiko.SFTP_OK

    def rename(self, oldpath, newpath):
        return paramiko.SFTP_OK

    def mkdir(self, path, attr):
        return paramiko.SFTP_OK

    def rmdir(self, path):
        return paramiko.SFTP_OK


def run_scp_sink(channel, handler):
    """Receive a file uploaded via `scp -t` (SCP sink protocol) and capture it."""
    ssh_port = config.get('ssh', {}).get('port', 22)
    max_upload = int(config.get('ssh', {}).get('max_upload_bytes', 50 * 1024 * 1024))
    try:
        channel.sendall(b'\x00')  # signal "ready"
        while True:
            line = b''
            while not line.endswith(b'\n'):
                ch = channel.recv(1)
                if not ch:
                    return
                line += ch
            line = line.rstrip(b'\r\n')
            if not line:
                continue
            kind = chr(line[0])
            if kind == 'C':
                # File header: C<mode> <size> <name>
                try:
                    _mode, size_s, name = line[1:].decode('utf-8', 'ignore').split(' ', 2)
                    size = int(size_s)
                except Exception:
                    channel.sendall(b'\x02scp: protocol error\n')
                    return
                channel.sendall(b'\x00')  # ack header
                data = bytearray()
                while len(data) < size:
                    chunk = channel.recv(min(65536, size - len(data)))
                    if not chunk:
                        break
                    data.extend(chunk)
                    if len(data) > max_upload:
                        break
                try:
                    channel.recv(1)  # trailing status byte from client
                except Exception:
                    pass
                channel.sendall(b'\x00')  # ack file received
                try:
                    process_uploaded_binary(
                        bytes(data[:max_upload]), name, handler.username, handler.password,
                        handler.client_address[0], handler.client_address[1],
                        ssh_port, 'ssh', 'SCP ' + name)
                except Exception as e:
                    logger.error("SCP upload processing error: " + str(e))
            elif kind in ('D', 'T'):
                channel.sendall(b'\x00')  # directory / mtime header: ack and ignore
            elif kind == 'E':
                channel.sendall(b'\x00')  # end of directory
            else:
                channel.sendall(b'\x00')
    except Exception as e:
        logger.error("SCP sink error: " + str(e))


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

        # In interactive mode with uploads allowed, expose the SFTP subsystem so
        # bots can upload binaries (captured and forwarded like FTP STOR).
        ssh_interactive = config.get('ssh', {}).get('interactive', False)
        upload_allowed = config.get('ssh', {}).get('allow_upload', True)
        if ssh_interactive and upload_allowed:
            transport.set_subsystem_handler('sftp', paramiko.SFTPServer, HoneypotSFTPServer)

        # Start server with custom handler (remember which local port was hit)
        try:
            local_port = client_socket.getsockname()[1]
        except Exception:
            local_port = config.get('ssh', {}).get('port', 22)
        server_handler = SSHServerHandler(client_address, local_port)
        transport.start_server(server=server_handler)

        # Wait for a channel (only opens if auth succeeded, i.e. interactive mode)
        channel = transport.accept(20)
        if channel is None:
            return

        try:
            # Let the client request a shell, run a command, or open SFTP
            server_handler.event.wait(10)

            if server_handler.sftp_requested:
                # SFTP runs in paramiko's own subsystem thread; keep the
                # connection alive until the client disconnects (bounded).
                deadline = time.time() + 900
                while transport.is_active() and time.time() < deadline:
                    time.sleep(1)
            elif server_handler.exec_command is not None:
                cmd = server_handler.exec_command
                if upload_allowed and re.match(r'\s*scp\b', cmd) and re.search(r'-[a-zA-Z]*t', cmd):
                    # File drop via `scp -t <path>`: capture the binary.
                    log_command(cmd, server_handler, True)
                    run_scp_sink(channel, server_handler)
                else:
                    # Non-interactive bot: a single command then close.
                    emu = ShellEmulator(server_handler.username,
                                        config.get('ssh', {}).get('hostname', DEFAULT_HOSTNAME))
                    output, _ = emu.execute(cmd)
                    log_command(cmd, server_handler, command_succeeded(output))
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


def process_uploaded_binary(file_bytes, filename, username, password,
                            source_ip, source_port, target_port, service_type, headers):
    """Hash an uploaded binary, log it, and forward it to the server (FTP STOR / SFTP put)."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    logger.info(f"{service_type.upper()} upload from {source_ip}: {filename} "
                f"({len(file_bytes)} bytes) sha256={file_hash}")

    queue_attack({
        'source_ip': source_ip, 'source_port': source_port, 'target_port': target_port,
        'username_attempt': username or "", 'password_attempt': password or "",
        'service_type': service_type, 'attack_type': 'file_upload', 'classification': 'file_upload',
        'malware_hash': file_hash, 'payload': filename,
    })

    send_file_to_server(file_bytes, filename, {
        'file_hash': file_hash,
        'file_name': filename or 'upload.bin',
        'file_size': str(len(file_bytes)),
        'source_ip': source_ip,
        'username': username or "",
        'password': password or "",
        'request_headers': (headers or "")[:8000],
        'agent_id': str(config.get('agent_id', 1)),
        'service_type': service_type,
    })


def _process_ftp_upload(file_bytes, filename, username, password, addr, ftp_port, cmd_log):
    """FTP STOR upload: delegate to the shared upload pipeline."""
    process_uploaded_binary(file_bytes, filename, username, password,
                            addr[0], addr[1], ftp_port, 'ftp', "\n".join(cmd_log))


# --- Malware collection: fake execution that fetches the real payload ---
_fetched_urls = set()
_fetched_lock = threading.Lock()
_URL_RE = re.compile(r'(?:https?|ftp)://[^\s\'"`|;()<>]+')
_DOLLAR = '\\' + chr(36)  # regex for a literal dollar, built without one (template-safe)


def fetch_downloads_from_text(text, username, password, source_ip, source_port):
    """
    Find download URLs in a command/script and fetch+upload the payload.

    The bot's wget/curl/tftp "succeeds" (fake execution), but behind the scenes
    the agent downloads the targeted file and ships it to the server for
    analysis (hashed, deduplicated) like any other captured payload.
    """
    ssh_cfg = config.get('ssh', {})
    if not ssh_cfg.get('allow_upload', True) or not ssh_cfg.get('fetch_downloads', True):
        return
    urls = set()
    for raw in _URL_RE.findall(text or ''):
        # Substitute common arch placeholders so arch-based payload URLs resolve.
        u = re.sub(_DOLLAR + r'\((?:uname[^)]*|arch)\)', 'x86_64', raw)
        u = re.sub(_DOLLAR + r'\{?\w*arch\w*\}?', 'x86_64', u, flags=re.IGNORECASE)
        urls.add(u.rstrip('.,;'))
    for url in urls:
        threading.Thread(target=_fetch_one_download,
                         args=(url, username, password, source_ip, source_port),
                         daemon=True).start()


def _fetch_one_download(url, username, password, source_ip, source_port):
    with _fetched_lock:
        if url in _fetched_urls:
            return
        _fetched_urls.add(url)
        if len(_fetched_urls) > 5000:
            _fetched_urls.clear()
    max_size = int(config.get('ssh', {}).get('max_upload_bytes', 50 * 1024 * 1024))
    try:
        r = requests.get(url, timeout=20, verify=False, stream=True,
                         headers={'User-Agent': 'Wget/1.20.3 (linux-gnu)'})
        data = b''
        for chunk in r.iter_content(65536):
            if not chunk:
                break
            data += chunk
            if len(data) > max_size:
                break
        if not data:
            logger.info("Download empty: " + url)
            return
        name = url.rsplit('/', 1)[-1].split('?')[0] or 'download.bin'
        logger.info("Fetched payload from %s (%d bytes)" % (url, len(data)))
        process_uploaded_binary(data, name, username, password, source_ip, source_port,
                                config.get('ssh', {}).get('port', 22), 'ssh', 'fetched: ' + url)
    except Exception as e:
        logger.error("Payload fetch failed for %s: %s" % (url, e))


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
    try:
        ftp_port = conn.getsockname()[1]
    except Exception:
        ftp_port = ftp_cfg.get('port', 21)
    interactive_enabled = ftp_cfg.get('interactive', False)
    upload_allowed = ftp_cfg.get('allow_upload', True)
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
                    # Always capture the credential attempt (never disabled).
                    logger.info(f"FTP auth attempt from {addr[0]}: {username}:{password}")
                    queue_attack({
                        'source_ip': addr[0], 'source_port': addr[1], 'target_port': ftp_port,
                        'username_attempt': username or "", 'password_attempt': password or "",
                        'service_type': 'ftp', 'attack_type': 'auth_attempt',
                        'classification': 'auth_attempt',
                    })
                    # Interactive mode: granted to a single whitelisted bot at a time.
                    if (interactive_enabled and _auth_allowed(username or "", password or "")
                            and not authenticated and ftp_interactive_lock.acquire(blocking=False)):
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
                    elif not upload_allowed:
                        send("550 Permission denied.\r\n")
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
                                        logger.warning(f"FTP upload truncated (>{max_size} bytes) from {addr[0]}")
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
                                logger.error(f"Upload processing error: {e}")
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

def _ssh_accept_loop(ssh_host, ssh_port):
    """Bind one SSH port and accept connections forever."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((ssh_host, ssh_port))
    except OSError as e:
        logger.error(f"Failed to bind SSH port {ssh_port}: {e} (need sudo for ports < 1024)")
        return
    server_socket.listen(100)
    logger.info(f"SSH Honeypot listening on port {ssh_port}")
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            logger.info(f"SSH connection from {client_address[0]}:{client_address[1]} on port {ssh_port}")
            threading.Thread(target=handle_client_ssh, args=(client_socket, client_address), daemon=True).start()
    except Exception as e:
        logger.error(f"SSH accept loop error on port {ssh_port}: {e}")
    finally:
        server_socket.close()


def start_ssh_honeypot():
    """Start the SSH honeypot on every configured port."""
    if not config.get('features', {}).get('ssh_enabled', True):
        logger.info("SSH honeypot is disabled in configuration")
        return

    ssh_host = config.get('ssh', {}).get('host', '0.0.0.0')
    if _in_container():
        ssh_host = '0.0.0.0'  # the configured host IP isn't bindable inside a container
    ports = _service_ports('ssh', 22)
    logger.info(f"Starting SSH Honeypot on {ssh_host} ports {ports}")
    logger.info(f"Agent ID: {config.get('agent_id', 1)}")

    load_or_generate_host_key()

    threads = []
    for p in ports:
        t = threading.Thread(target=_ssh_accept_loop, args=(ssh_host, p), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def _ftp_accept_loop(ftp_host, ftp_port):
    """Bind one FTP port and accept connections forever."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((ftp_host, ftp_port))
    except OSError as e:
        logger.error(f"Failed to bind FTP port {ftp_port}: {e} (need sudo for ports < 1024)")
        return
    s.listen(100)
    logger.info(f"FTP Honeypot listening on port {ftp_port}")
    try:
        while True:
            conn, addr = s.accept()
            logger.info(f"FTP connection from {addr[0]}:{addr[1]} on port {ftp_port}")
            threading.Thread(target=handle_client_ftp, args=(conn, addr), daemon=True).start()
    except Exception as e:
        logger.error(f"FTP accept loop error on port {ftp_port}: {e}")
    finally:
        s.close()


def start_ftp_honeypot():
    """Start the FTP honeypot on every configured port."""
    if not config.get('features', {}).get('ftp_enabled', True):
        logger.info("FTP honeypot is disabled in configuration")
        return

    ftp_host = config.get('ftp', {}).get('host', '0.0.0.0')
    if _in_container():
        ftp_host = '0.0.0.0'  # the configured host IP isn't bindable inside a container
    ports = _service_ports('ftp', 21)
    logger.info(f"Starting FTP Honeypot on {ftp_host} ports {ports}")

    threads = []
    for p in ports:
        t = threading.Thread(target=_ftp_accept_loop, args=(ftp_host, p), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()




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
