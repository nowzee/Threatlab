from module.database.db_manager import DatabaseManagerHoneypot
from datetime import datetime, timedelta
from collections import Counter
import re


def is_valid_ip(ip_string: str) -> bool:
    """Vérifie si la chaîne est une adresse IP valide"""
    # Regex validates IPv4 format: 4 groups of 1-3 digits separated by dots
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip_string):
        return False
    # Check that each octet is in valid range 0-255
    parts = ip_string.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def search_ip(ip_address: str) -> dict:
    """
    Recherche toutes les informations liées à une adresse IP
    """
    with DatabaseManagerHoneypot() as db:
        # Informations générales sur l'IP
        db.execute("""
            SELECT
                ip_address,
                country_name,
                country_code,
                first_seen,
                last_seen,
                total_attack_count,
                classification
            FROM malicious_ips
            WHERE ip_address = ?
        """, (ip_address,))

        ip_info = db.fetchone()

        if not ip_info:
            # Si l'IP n'est pas dans malicious_ips, chercher dans attack_logs
            db.execute("""
                SELECT
                    source_ip,
                    country_name,
                    country_code,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_seen,
                    COUNT(*) as total_count
                FROM attack_logs
                WHERE source_ip = ?
                GROUP BY source_ip, country_name, country_code
            """, (ip_address,))

            ip_info = db.fetchone()

            if not ip_info:
                return None

        # Passwords utilisés par cette IP
        db.execute("""
            SELECT
                password_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = ? AND password_attempt IS NOT NULL AND password_attempt != ''
            GROUP BY password_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (ip_address,))

        passwords = []
        for row in db.fetchall():
            passwords.append({
                "password": row[0],
                "count": row[1]
            })

        # Usernames utilisés par cette IP
        db.execute("""
            SELECT
                username_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = ? AND username_attempt IS NOT NULL AND username_attempt != ''
            GROUP BY username_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (ip_address,))

        usernames = []
        for row in db.fetchall():
            usernames.append({
                "username": row[0],
                "count": row[1]
            })

        # Services ciblés
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = ?
            GROUP BY service_type
            ORDER BY count DESC
        """, (ip_address,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row[0],
                "count": row[1]
            })

        # Calculate activity metrics across different time periods for trending
        now = datetime.now()

        # Count attacks in last 24 hours
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (ip_address,))
        last_24h = db.fetchone()[0]

        # Count attacks in last 7 days
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (ip_address,))
        last_7d = db.fetchone()[0]

        # Count attacks in last 30 days
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (ip_address,))
        last_30d = db.fetchone()[0]

        return {
            "type": "ip",
            "value": ip_info[0],
            "country": ip_info[1] if ip_info[1] else "Inconnu",
            "country_code": ip_info[2] if len(ip_info) > 2 and ip_info[2] else None,
            "first_seen": ip_info[3],
            "last_seen": ip_info[4],
            "total_count": ip_info[5] if len(ip_info) > 5 else ip_info[5],
            "classification": ip_info[6] if len(ip_info) > 6 and ip_info[6] else "IP Malveillante",
            "related_passwords": passwords,
            "related_usernames": usernames,
            "targeted_services": services,
            "activity": {
                "last24h": last_24h,
                "last7d": last_7d,
                "last30d": last_30d
            }
        }


def search_password(password: str) -> dict:
    """
    Recherche toutes les informations liées à un mot de passe
    """
    with DatabaseManagerHoneypot() as db:
        # Nombre total d'utilisations
        db.execute("""
            SELECT
                COUNT(*) as total_count,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM attack_logs
            WHERE password_attempt = ?
        """, (password,))

        info = db.fetchone()

        if not info or info[0] == 0:
            return None

        # IPs qui ont utilisé ce password
        db.execute("""
            SELECT
                source_ip,
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = ?
            GROUP BY source_ip, country_name
            ORDER BY count DESC
            LIMIT 30
        """, (password,))

        ips = []
        for row in db.fetchall():
            ips.append({
                "ip": row[0],
                "country": row[1] if row[1] else "Inconnu",
                "count": row[2]
            })

        # Usernames associés
        db.execute("""
            SELECT
                username_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = ? AND username_attempt IS NOT NULL AND username_attempt != ''
            GROUP BY username_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (password,))

        usernames = []
        for row in db.fetchall():
            usernames.append({
                "username": row[0],
                "count": row[1]
            })

        # Services où ce password a été tenté
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = ?
            GROUP BY service_type
            ORDER BY count DESC
        """, (password,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row[0],
                "count": row[1]
            })

        # Pays d'origine
        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = ? AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (password,))

        countries = []
        total_with_country = sum([row[1] for row in db.fetchall()])

        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = ? AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (password,))

        for row in db.fetchall():
            percentage = (row[1] / total_with_country * 100) if total_with_country > 0 else 0
            countries.append({
                "country": row[0],
                "count": row[1],
                "percentage": round(percentage, 1)
            })

        # Timeline d'activité
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE password_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (password,))
        last_24h = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE password_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (password,))
        last_7d = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE password_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (password,))
        last_30d = db.fetchone()[0]

        return {
            "type": "password",
            "value": password,
            "total_count": info[0],
            "first_seen": info[1],
            "last_seen": info[2],
            "related_ips": ips,
            "related_usernames": usernames,
            "targeted_services": services,
            "origin_countries": countries,
            "activity": {
                "last24h": last_24h,
                "last7d": last_7d,
                "last30d": last_30d
            }
        }


def search_username(username: str) -> dict:
    """
    Recherche toutes les informations liées à un nom d'utilisateur
    """
    with DatabaseManagerHoneypot() as db:
        # Nombre total d'utilisations
        db.execute("""
            SELECT
                COUNT(*) as total_count,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM attack_logs
            WHERE username_attempt = ?
        """, (username,))

        info = db.fetchone()

        if not info or info[0] == 0:
            return None

        # IPs qui ont utilisé ce username
        db.execute("""
            SELECT
                source_ip,
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = ?
            GROUP BY source_ip, country_name
            ORDER BY count DESC
            LIMIT 30
        """, (username,))

        ips = []
        for row in db.fetchall():
            ips.append({
                "ip": row[0],
                "country": row[1] if row[1] else "Inconnu",
                "count": row[2]
            })

        # Passwords associés
        db.execute("""
            SELECT
                password_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = ? AND password_attempt IS NOT NULL AND password_attempt != ''
            GROUP BY password_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (username,))

        passwords = []
        for row in db.fetchall():
            passwords.append({
                "password": row[0],
                "count": row[1]
            })

        # Services où ce username a été tenté
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = ?
            GROUP BY service_type
            ORDER BY count DESC
        """, (username,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row[0],
                "count": row[1]
            })

        # Pays d'origine
        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = ? AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (username,))

        countries = []
        total_with_country = sum([row[1] for row in db.fetchall()])

        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = ? AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (username,))

        for row in db.fetchall():
            percentage = (row[1] / total_with_country * 100) if total_with_country > 0 else 0
            countries.append({
                "country": row[0],
                "count": row[1],
                "percentage": round(percentage, 1)
            })

        # Timeline d'activité
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE username_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (username,))
        last_24h = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE username_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (username,))
        last_7d = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE username_attempt = ?
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (username,))
        last_30d = db.fetchone()[0]

        return {
            "type": "username",
            "value": username,
            "total_count": info[0],
            "first_seen": info[1],
            "last_seen": info[2],
            "related_ips": ips,
            "related_passwords": passwords,
            "targeted_services": services,
            "origin_countries": countries,
            "activity": {
                "last24h": last_24h,
                "last7d": last_7d,
                "last30d": last_30d
            }
        }


def get_ip_timeline(ip_address: str, timeline: str = "24h") -> list:
    """
    Récupère les données temporelles pour une IP spécifique
    """
    with DatabaseManagerHoneypot() as db:
        # Map timeline parameter to MySQL datetime expression
        if timeline == "24h":
            time_filter = "DATE_SUB(NOW(), INTERVAL 1 DAY)"
        elif timeline == "7d":
            time_filter = "DATE_SUB(NOW(), INTERVAL 7 DAY)"
        elif timeline == "30d":
            time_filter = "DATE_SUB(NOW(), INTERVAL 30 DAY)"
        else:  # "all" or other - get all historical data
            time_filter = "'1970-01-01 00:00:00'"  # Unix epoch start

        # Fetch all attack timestamps for this IP in the time range
        db.execute(f"""
            SELECT created_at
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= {time_filter}
            ORDER BY created_at ASC
        """, (ip_address,))

        logs = db.fetchall()

        # Process logs to create timeline with proper bucketing
        data = []
        now = datetime.now()
        period_counts = Counter()

        if logs:
            for log in logs:
                # Handle both datetime objects (MySQL) and strings (SQLite)
                if isinstance(log[0], datetime):
                    created_at = log[0]
                else:
                    try:
                        # Try parsing with microseconds first
                        created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        try:
                            # Fallback to parsing without microseconds
                            created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            continue

                # Group attacks into time buckets: hourly for 24h, daily for longer periods
                if timeline == "24h":
                    # Round down to the hour for hourly buckets
                    period_key = created_at.replace(minute=0, second=0, microsecond=0)
                else:
                    # Round down to the day for daily buckets
                    period_key = created_at.replace(hour=0, minute=0, second=0, microsecond=0)

                period_counts[period_key] += 1

        # Generate complete timeline with zeros for periods without attacks
        # This ensures charts display correctly with continuous time axis
        if timeline == "24h":
            periods = 24
            # Iterate backwards from now to 24 hours ago
            for i in range(periods - 1, -1, -1):
                period = now - timedelta(hours=i)
                key = period.replace(minute=0, second=0, microsecond=0)
                label = f"{period.hour:02d}:00"
                count = period_counts.get(key, 0)  # 0 if no attacks in this hour

                data.append({
                    "time": period.isoformat(),
                    "label": label,
                    "count": count
                })
        elif timeline == "7d":
            periods = 7
            for i in range(periods - 1, -1, -1):
                period = now - timedelta(days=i)
                key = period.replace(hour=0, minute=0, second=0, microsecond=0)
                label = f"{period.day:02d}/{period.month:02d}"
                count = period_counts.get(key, 0)

                data.append({
                    "time": period.isoformat(),
                    "label": label,
                    "count": count
                })
        elif timeline == "30d":
            periods = 30
            for i in range(periods - 1, -1, -1):
                period = now - timedelta(days=i)
                key = period.replace(hour=0, minute=0, second=0, microsecond=0)
                label = f"{period.day:02d}/{period.month:02d}"
                count = period_counts.get(key, 0)

                data.append({
                    "time": period.isoformat(),
                    "label": label,
                    "count": count
                })
        else:  # "all" - grouper par jour depuis le début
            if logs and len(logs) > 0:
                # Trouver la première date - handle both datetime objects and strings
                if isinstance(logs[0][0], datetime):
                    first_date = logs[0][0]
                else:
                    try:
                        first_date = datetime.strptime(logs[0][0], "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        first_date = datetime.strptime(logs[0][0], "%Y-%m-%d %H:%M:%S")

                first_date = first_date.replace(hour=0, minute=0, second=0, microsecond=0)
                current_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                days_diff = (current_date - first_date).days

                # Limiter à 365 jours max pour éviter trop de données
                if days_diff > 365:
                    days_diff = 365
                    first_date = current_date - timedelta(days=365)

                for i in range(days_diff, -1, -1):
                    period = now - timedelta(days=i)
                    key = period.replace(hour=0, minute=0, second=0, microsecond=0)
                    label = f"{period.day:02d}/{period.month:02d}"
                    count = period_counts.get(key, 0)

                    data.append({
                        "time": period.isoformat(),
                        "label": label,
                        "count": count
                    })

        return data
