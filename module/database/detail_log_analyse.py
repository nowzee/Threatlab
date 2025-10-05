from module.database.db_manager import DatabaseManagerHoneypot

def last_log_analyse(timeline):
    global interval

    if timeline == '24h':
        interval = "-1 day"
    elif timeline == '7d':
        interval = "-7 day"
    elif timeline == '30d':
        interval = "-30 day"

    with DatabaseManagerHoneypot() as db:
        db.execute("SELECT created_at, country_code, country_name, agent_id  "
                   "FROM attack_logs WHERE created_at >= datetime('now', ?) ORDER BY created_at DESC", (interval,))
        result = db.fetchall()
        if not result:
            return False

        return result

def get_alerts_list(limit=50):
    """
    Récupère la liste des dernières alertes depuis attack_logs
    """
    with DatabaseManagerHoneypot() as db:
        db.execute("""
            SELECT
                id,
                created_at,
                agent_id,
                source_ip,
                target_port,
                service_type,
                country_name
            FROM attack_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        results = db.fetchall()

        alerts = []
        for row in results:
            alerts.append({
                "id": row[0],
                "timestamp": row[1],
                "agent_id": row[2],
                "source_ip": row[3],
                "target_port": row[4],
                "service_type": row[5],
                "country_name": row[6] if row[6] else "Inconnu"
            })

        return alerts

def get_alert_detail_by_id(alert_id):
    """
    Récupère les détails complets d'une alerte spécifique
    """
    with DatabaseManagerHoneypot() as db:
        db.execute("""
            SELECT
                al.id,
                al.created_at,
                al.agent_id,
                al.source_ip,
                al.source_port,
                al.target_port,
                al.service_type,
                al.username_attempt,
                al.password_attempt,
                al.payload,
                al.command,
                al.country_code,
                al.country_name,
                al.attack_type,
                ha.agent_name
            FROM attack_logs al
            LEFT JOIN honey_agents ha ON al.agent_id = ha.id
            WHERE al.id = ?
        """, (alert_id,))

        result = db.fetchone()

        if not result:
            return None

        alert_detail = {
            "id": result[0],
            "timestamp": result[1],
            "agent_id": result[2],
            "agent_name": result[14] if result[14] else f"Agent {result[2]}",
            "source_ip": result[3],
            "source_port": result[4],
            "target_port": result[5],
            "service_type": result[6],
            "username_attempt": result[7],
            "password_attempt": result[8],
            "payload": result[9],
            "command": result[10],
            "country_code": result[11],
            "country_name": result[12] if result[12] else "Inconnu",
            "attack_type": result[13]
        }

        return alert_detail