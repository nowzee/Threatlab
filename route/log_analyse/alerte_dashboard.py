"""
Alert Dashboard Route Module.

This module provides Flask routes for log analysis and alert visualization,
including timeline data for charts and alert lists.
"""

from typing import List, Dict, Any, Tuple
from flask import Blueprint, jsonify, request, Response
from datetime import datetime, timedelta
from collections import Counter
from module.database.detail_log_analyse import last_log_analyse, get_alerts_list

log_analyse_bp = Blueprint("log_analyse_bp", __name__, url_prefix="/log-analyse")


@log_analyse_bp.route("/get_data_chart", methods=["POST"])
def get_data() -> Response:
    """
    Retrieve timeline data for chart visualization.

    This endpoint processes attack logs and groups them by time periods
    (hourly for 24h, daily for 7d/30d) to create chart data.

    Expects JSON body with:
    - time: Timeline period ('24h', '7d', or '30d')

    Returns:
        JSON array of time periods with attack counts for visualization.
        Each entry contains:
        - time: ISO format timestamp
        - label: Human-readable time label
        - count: Number of attacks in that period
    """
    req_data = request.get_json()
    timeline = req_data.get("time", "24h")

    # Get logs from database for the requested timeline
    logs = last_log_analyse(timeline)

    # Process logs to create timeline
    data: List[Dict[str, Any]] = []
    now = datetime.now()

    # Count logs per period (hourly for 24h, daily for 7d/30d)
    period_counts: Counter = Counter()

    if logs:
        for log in logs:
            try:
                # Timestamp is the first element of the tuple
                created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

            # Group by hour for 24h, by day for 7d and 30d
            if timeline == "24h":
                period_key = created_at.replace(minute=0, second=0, microsecond=0)
            else:  # 7d or 30d
                period_key = created_at.replace(hour=0, minute=0, second=0, microsecond=0)

            period_counts[period_key] += 1

    # Generate complete timeline with zeros for periods without logs
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
