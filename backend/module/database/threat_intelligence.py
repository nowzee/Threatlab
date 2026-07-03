from module.database.db_manager import DatabaseManagerHoneypot
from module.database.detail_log_analyse import get_db_now
from datetime import datetime, timedelta
import re


def is_valid_ip(ip_string: str) -> bool:
    """Checks whether the string is a valid IP address"""
    # Regex validates IPv4 format: 4 groups of 1-3 digits separated by dots
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip_string):
        return False
    # Check that each octet is in valid range 0-255
    parts = ip_string.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def search_ip(ip_address: str) -> dict:
    """
    Searches for all information related to an IP address
    """
    with DatabaseManagerHoneypot() as db:
        # General information about the IP
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
            WHERE ip_address = %s
        """, (ip_address,))

        ip_info = db.fetchone()

        if not ip_info:
            # If the IP is not in malicious_ips, search in attack_logs
            db.execute("""
                SELECT
                    source_ip,
                    country_name,
                    country_code,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_seen,
                    COUNT(*) as total_count
                FROM attack_logs
                WHERE source_ip = %s
                GROUP BY source_ip, country_name, country_code
            """, (ip_address,))

            ip_info = db.fetchone()

            if not ip_info:
                return None

        # Passwords used by this IP
        db.execute("""
            SELECT
                password_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s AND password_attempt IS NOT NULL AND password_attempt != ''
            GROUP BY password_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (ip_address,))

        passwords = []
        for row in db.fetchall():
            passwords.append({
                "password": row['password_attempt'],
                "count": row['count']
            })

        # Usernames used by this IP
        db.execute("""
            SELECT
                username_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s AND username_attempt IS NOT NULL AND username_attempt != ''
            GROUP BY username_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (ip_address,))

        usernames = []
        for row in db.fetchall():
            usernames.append({
                "username": row['username_attempt'],
                "count": row['count']
            })

        # Targeted services
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s
            GROUP BY service_type
            ORDER BY count DESC
        """, (ip_address,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row['service_type'],
                "count": row['count']
            })

        # Calculate activity metrics across different time periods for trending
        now = datetime.now()

        # Count attacks in last 24 hours
        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (ip_address,))
        last_24h = db.fetchone()['count']

        # Count attacks in last 7 days
        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (ip_address,))
        last_7d = db.fetchone()['count']

        # Count attacks in last 30 days
        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE source_ip = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (ip_address,))
        last_30d = db.fetchone()['count']

        return {
            "type": "ip",
            "value": ip_info['ip_address'],
            "country": ip_info['country_name'] if ip_info.get('country_name') else "Inconnu",
            "country_code": ip_info.get('country_code'),
            "first_seen": ip_info['first_seen'],
            "last_seen": ip_info['last_seen'],
            "total_count": ip_info.get('total_attack_count', ip_info.get('total_count', 0)),
            "classification": ip_info.get('classification', 'IP Malveillante'),
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
    Searches for all information related to a password
    """
    with DatabaseManagerHoneypot() as db:
        # Total number of uses
        db.execute("""
            SELECT
                COUNT(*) as total_count,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM attack_logs
            WHERE password_attempt = %s
        """, (password,))

        info = db.fetchone()

        if not info or info['total_count'] == 0:
            return None

        # IPs that used this password
        db.execute("""
            SELECT
                source_ip,
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s
            GROUP BY source_ip, country_name
            ORDER BY count DESC
            LIMIT 30
        """, (password,))

        ips = []
        for row in db.fetchall():
            ips.append({
                "ip": row['source_ip'],
                "country": row['country_name'] if row.get('country_name') else "Inconnu",
                "count": row['count']
            })

        # Associated usernames
        db.execute("""
            SELECT
                username_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s AND username_attempt IS NOT NULL AND username_attempt != ''
            GROUP BY username_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (password,))

        usernames = []
        for row in db.fetchall():
            usernames.append({
                "username": row['username_attempt'],
                "count": row['count']
            })

        # Services where this password was attempted
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s
            GROUP BY service_type
            ORDER BY count DESC
        """, (password,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row['service_type'],
                "count": row['count']
            })

        # Origin countries
        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (password,))

        countries = []
        total_with_country = sum([row['count'] for row in db.fetchall()])

        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (password,))

        for row in db.fetchall():
            percentage = (row['count'] / total_with_country * 100) if total_with_country > 0 else 0
            countries.append({
                "country": row['country_name'],
                "count": row['count'],
                "percentage": round(percentage, 1)
            })

        # Activity timeline
        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (password,))
        last_24h = db.fetchone()['count']

        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (password,))
        last_7d = db.fetchone()['count']

        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE password_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (password,))
        last_30d = db.fetchone()['count']

        return {
            "type": "password",
            "value": password,
            "total_count": info['total_count'],
            "first_seen": info['first_seen'],
            "last_seen": info['last_seen'],
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
    Searches for all information related to a username
    """
    with DatabaseManagerHoneypot() as db:
        # Total number of uses
        db.execute("""
            SELECT
                COUNT(*) as total_count,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM attack_logs
            WHERE username_attempt = %s
        """, (username,))

        info = db.fetchone()

        if not info or info['total_count'] == 0:
            return None

        # IPs that used this username
        db.execute("""
            SELECT
                source_ip,
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s
            GROUP BY source_ip, country_name
            ORDER BY count DESC
            LIMIT 30
        """, (username,))

        ips = []
        for row in db.fetchall():
            ips.append({
                "ip": row['source_ip'],
                "country": row['country_name'] if row.get('country_name') else "Inconnu",
                "count": row['count']
            })

        # Associated passwords
        db.execute("""
            SELECT
                password_attempt,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s AND password_attempt IS NOT NULL AND password_attempt != ''
            GROUP BY password_attempt
            ORDER BY count DESC
            LIMIT 20
        """, (username,))

        passwords = []
        for row in db.fetchall():
            passwords.append({
                "password": row['password_attempt'],
                "count": row['count']
            })

        # Services where this username was attempted
        db.execute("""
            SELECT
                service_type,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s
            GROUP BY service_type
            ORDER BY count DESC
        """, (username,))

        services = []
        for row in db.fetchall():
            services.append({
                "service": row['service_type'],
                "count": row['count']
            })

        # Origin countries
        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (username,))

        countries = []
        total_with_country = sum([row['count'] for row in db.fetchall()])

        db.execute("""
            SELECT
                country_name,
                COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s AND country_name IS NOT NULL
            GROUP BY country_name
            ORDER BY count DESC
            LIMIT 10
        """, (username,))

        for row in db.fetchall():
            percentage = (row['count'] / total_with_country * 100) if total_with_country > 0 else 0
            countries.append({
                "country": row['country_name'],
                "count": row['count'],
                "percentage": round(percentage, 1)
            })

        # Activity timeline
        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """, (username,))
        last_24h = db.fetchone()['count']

        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (username,))
        last_7d = db.fetchone()['count']

        db.execute("""
            SELECT COUNT(*) as count
            FROM attack_logs
            WHERE username_attempt = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, (username,))
        last_30d = db.fetchone()['count']

        return {
            "type": "username",
            "value": username,
            "total_count": info['total_count'],
            "first_seen": info['first_seen'],
            "last_seen": info['last_seen'],
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
    Retrieves the time-series data for a specific IP
    """
    if timeline == "24h":
        time_filter = "DATE_SUB(NOW(), INTERVAL 1 DAY)"
        bucket_fmt = "%Y-%m-%d %H:00:00"
    elif timeline == "7d":
        time_filter = "DATE_SUB(NOW(), INTERVAL 7 DAY)"
        bucket_fmt = "%Y-%m-%d"
    elif timeline == "30d":
        time_filter = "DATE_SUB(NOW(), INTERVAL 30 DAY)"
        bucket_fmt = "%Y-%m-%d"
    else:  # "all" or other - all historical data, daily buckets
        time_filter = "'1970-01-01 00:00:00'"
        bucket_fmt = "%Y-%m-%d"

    with DatabaseManagerHoneypot() as db:
        db.execute(
            f"SELECT DATE_FORMAT(created_at, %s) AS bucket, COUNT(*) AS c "
            f"FROM attack_logs "
            f"WHERE source_ip = %s AND created_at >= {time_filter} "
            f"GROUP BY bucket",
            (bucket_fmt, ip_address))
        counts = {row['bucket']: row['c'] for row in db.fetchall()}

        first_local = None
        if timeline not in ("24h", "7d", "30d"):
            db.execute(
                "SELECT DATE_FORMAT(MIN(created_at), %s) AS d "
                "FROM attack_logs WHERE source_ip = %s",
                ("%Y-%m-%d", ip_address))
            row = db.fetchone()
            first_local = row['d'] if row else None

    now = get_db_now()
    data = []

    if timeline == "24h":
        for i in range(23, -1, -1):
            period = now - timedelta(hours=i)
            key = period.strftime("%Y-%m-%d %H:00:00")
            data.append({"time": period.isoformat(),
                         "label": f"{period.hour:02d}:00",
                         "count": counts.get(key, 0)})
    elif timeline in ("7d", "30d"):
        periods = 7 if timeline == "7d" else 30
        for i in range(periods - 1, -1, -1):
            period = now - timedelta(days=i)
            key = period.strftime("%Y-%m-%d")
            data.append({"time": period.isoformat(),
                         "label": f"{period.day:02d}/{period.month:02d}",
                         "count": counts.get(key, 0)})
    else:  # "all"
        if first_local:
            first_day = datetime.strptime(first_local, "%Y-%m-%d").date()
            days_diff = (now.date() - first_day).days
            if days_diff > 365:
                days_diff = 365
            for i in range(days_diff, -1, -1):
                period = now - timedelta(days=i)
                key = period.strftime("%Y-%m-%d")
                data.append({"time": period.isoformat(),
                             "label": f"{period.day:02d}/{period.month:02d}",
                             "count": counts.get(key, 0)})

    return data
