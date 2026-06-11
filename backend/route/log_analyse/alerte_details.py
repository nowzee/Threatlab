"""
Alert Details Route Module.

This module provides Flask routes for retrieving detailed information
about specific security alerts.
"""

from typing import Tuple
from flask import Blueprint, jsonify, Response
from module.database.detail_log_analyse import get_alert_detail_by_id

alert_details_bp = Blueprint("alert_details_bp", __name__, url_prefix="/log-analyse")


@alert_details_bp.route("/alert/<int:alert_id>", methods=["GET"])
def get_alert_details(alert_id: int) -> Tuple[Response, int]:
    """
    Retrieve detailed information for a specific alert.

    Args:
        alert_id: The ID of the alert to retrieve.

    Returns:
        JSON object with complete alert details including:
        - Attack information (source IP, ports, service type)
        - Credentials attempted (username, password)
        - Payload and command data
        - Geographic information (country code, country name)
        - Agent information
        HTTP status codes: 200 (success), 404 (alert not found).
    """
    alert_detail = get_alert_detail_by_id(alert_id)

    if alert_detail is None:
        return jsonify({"error": "Alerte introuvable"}), 404

    return jsonify(alert_detail), 200
