"""
Alert Dashboard Route Module.

This module provides Flask routes for log analysis and alert visualization,
including timeline data for charts and alert lists.
"""

from typing import List, Dict, Any, Tuple
from flask import Blueprint, jsonify, request, Response
from datetime import timedelta
from module.database.detail_log_analyse import get_attack_counts_by_bucket, get_alerts_list, get_db_now

log_analyse_bp = Blueprint("log_analyse_bp", __name__, url_prefix="/log-analyse")


@log_analyse_bp.route("/get_data_chart", methods=["POST"])
def get_data() -> Response:
    """
    Retrieve timeline data for chart visualization.

    Attacks are grouped by time period (hourly for 24h, daily for 7d/30d).

    Expects JSON body with:
    - time: Timeline period ('24h', '7d', or '30d')

    Returns:
        JSON array of {time, label, count} entries.
    """
    req_data = request.get_json()
    timeline = req_data.get("time", "24h")

    counts = get_attack_counts_by_bucket(timeline)
    now = get_db_now()
    data: List[Dict[str, Any]] = []

    if timeline == "24h":
        for i in range(23, -1, -1):
            period = now - timedelta(hours=i)
            key = period.strftime("%Y-%m-%d %H:00:00")
            data.append({
                "time": period.isoformat(),
                "label": f"{period.hour:02d}:00",
                "count": counts.get(key, 0),
            })
    elif timeline in ("7d", "30d"):
        periods = 7 if timeline == "7d" else 30
        for i in range(periods - 1, -1, -1):
            period = now - timedelta(days=i)
            key = period.strftime("%Y-%m-%d")
            data.append({
                "time": period.isoformat(),
                "label": f"{period.day:02d}/{period.month:02d}",
                "count": counts.get(key, 0),
            })

    return jsonify(data)


@log_analyse_bp.route("/alerts", methods=["GET"])
def get_alerts() -> Tuple[Response, int]:
    """
    Retrieve the list of recent alerts.

    Returns:
        JSON array of alert objects with details including timestamp,
        source IP, target port, service type, and country.
        HTTP status code 200.
    """
    alerts = get_alerts_list(limit=50)
    return jsonify(alerts), 200
