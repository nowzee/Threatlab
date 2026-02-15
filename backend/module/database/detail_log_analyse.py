"""
Detailed Log Analysis Module.

This module provides functions for retrieving and analyzing attack logs
from the honeypot database, including timeline queries and alert details.
"""

from typing import List, Dict, Any, Optional, Union
from module.database.db_manager import DatabaseManagerHoneypot


def last_log_analyse(timeline: str) -> Union[List[tuple], bool]:
    """
    Retrieve attack logs within a specified timeline.

    Args:
        timeline: The time period to query. Valid values are '24h', '7d', or '30d'.

    Returns:
        A list of tuples containing (created_at, country_code, country_name, agent_id)
        for each log entry, or False if no results are found.
    """
    # Map timeline strings to days
    if timeline == '24h':
        days = 1
    elif timeline == '7d':
        days = 7
    elif timeline == '30d':
        days = 30
    else:
        days = 1

    with DatabaseManagerHoneypot() as db:
        # Query logs from specified time period using MySQL's DATE_SUB
        db.execute("SELECT created_at, country_code, country_name, agent_id  "
                   "FROM attack_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY) ORDER BY created_at DESC", (days,))
        result = db.fetchall()
        if not result:
            return False

        return result


def get_alerts_list(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve the list of recent alerts from attack logs.

    Args:
        limit: Maximum number of alerts to retrieve. Defaults to 50.

    Returns:
        A list of dictionaries containing alert information with keys:
        - id: The alert ID
        - timestamp: When the attack occurred
        - agent_id: The honeypot agent ID
        - source_ip: The attacker's IP address
        - target_port: The targeted port
        - service_type: The service type (ssh, smtp, etc.)
        - country_name: The attacker's country or "Inconnu" if unknown
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


def get_alert_detail_by_id(alert_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve complete details for a specific alert.

    Args:
        alert_id: The ID of the alert to retrieve.

    Returns:
        A dictionary containing detailed alert information including:
        - id, timestamp, agent_id, agent_name
        - source_ip, source_port, target_port
        - service_type, username_attempt, password_attempt
        - payload, command, country_code, country_name, attack_type
        Returns None if the alert is not found.
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