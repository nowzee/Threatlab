from module.database.db_manager import DatabaseManagerHoneypot
from datetime import datetime, timedelta
from collections import Counter
import re


def is_valid_ip(ip_string: str) -> bool:
    """Vérifie si la chaîne est une adresse IP valide"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip_string):
        return False
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

        # Timeline d'activité
        now = datetime.now()

        # Dernières 24h
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= datetime('now', '-1 day')
        """, (ip_address,))
        last_24h = db.fetchone()[0]

        # Derniers 7 jours
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= datetime('now', '-7 day')
        """, (ip_address,))
        last_7d = db.fetchone()[0]

        # Derniers 30 jours
        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= datetime('now', '-30 day')
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
            AND created_at >= datetime('now', '-1 day')
        """, (password,))
        last_24h = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE password_attempt = ?
            AND created_at >= datetime('now', '-7 day')
        """, (password,))
        last_7d = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE password_attempt = ?
            AND created_at >= datetime('now', '-30 day')
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
            AND created_at >= datetime('now', '-1 day')
        """, (username,))
        last_24h = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE username_attempt = ?
            AND created_at >= datetime('now', '-7 day')
        """, (username,))
        last_7d = db.fetchone()[0]

        db.execute("""
            SELECT COUNT(*)
            FROM attack_logs
            WHERE username_attempt = ?
            AND created_at >= datetime('now', '-30 day')
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
        # Déterminer la période de temps
        if timeline == "24h":
            time_filter = "datetime('now', '-1 day')"
        elif timeline == "7d":
            time_filter = "datetime('now', '-7 day')"
        elif timeline == "30d":
            time_filter = "datetime('now', '-30 day')"
        else:  # "all" ou autre
            time_filter = "datetime('1970-01-01')"  # Depuis le début

        # Récupérer tous les logs pour cette IP
        db.execute(f"""
            SELECT created_at
            FROM attack_logs
            WHERE source_ip = ?
            AND created_at >= {time_filter}
            ORDER BY created_at ASC
        """, (ip_address,))

        logs = db.fetchall()

        # Traitement des logs pour créer la timeline
        data = []
        now = datetime.now()
        period_counts = Counter()

        if logs:
            for log in logs:
                try:
                    created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue

                # Grouper par heure pour 24h, par jour pour le reste
                if timeline == "24h":
                    period_key = created_at.replace(minute=0, second=0, microsecond=0)
                else:
                    period_key = created_at.replace(hour=0, minute=0, second=0, microsecond=0)

                period_counts[period_key] += 1

        # Générer la timeline complète avec des zéros pour les périodes sans logs
        if timeline == "24h":
            periods = 24
            for i in range(periods - 1, -1, -1):
                period = now - timedelta(hours=i)
                key = period.replace(minute=0, second=0, microsecond=0)
                label = f"{period.hour:02d}:00"
                count = period_counts.get(key, 0)

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
                # Trouver la première date
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
