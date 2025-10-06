"""
Threat Intelligence Route Module.

This module provides Flask routes for cyber threat intelligence lookups,
including IP address, password, and username searches, as well as timeline data.
"""

from typing import Tuple, Optional
from flask import Blueprint, jsonify, request, Response
from module.database.threat_intelligence import search_ip, search_password, search_username, is_valid_ip, get_ip_timeline

threat_intel_bp = Blueprint("threat_intel_bp", __name__, url_prefix="/api/threat-intel")


@threat_intel_bp.route("/search", methods=["POST"])
def search() -> Tuple[Response, int]:
    """
    Unified search endpoint for IP addresses, passwords, or usernames.

    This endpoint can automatically detect the query type or use a specified type.
    It searches the threat intelligence database for matching indicators.

    Expects JSON body with:
    - query: The search term (IP, password, or username)
    - type: Optional search type ('ip', 'password', 'username', or 'auto')

    Returns:
        JSON response with threat intelligence data if found, or error message.
        HTTP status codes: 200 (found), 400 (invalid format), 404 (not found), 500 (error).
    """
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        search_type = data.get("type", "auto").strip()

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        result: Optional[dict] = None

        # Search strategy depends on specified type or auto-detection
        if search_type == "ip":
            # Explicit IP search - validate format first
            if not is_valid_ip(query):
                return jsonify({
                    "error": "Invalid IP format",
                    "message": f"'{query}' n'est pas une adresse IP valide"
                }), 400
            result = search_ip(query)
        elif search_type == "password":
            # Explicit password search
            result = search_password(query)
        elif search_type == "username":
            # Explicit username search
            result = search_username(query)
        else:
            # Auto mode: try to detect query type and search accordingly
            # Priority order: IP > Password > Username

            # 1. Try IP search if format matches
            if is_valid_ip(query):
                result = search_ip(query)
                if result:
                    return jsonify(result), 200

            # 2. Try password search
            result = search_password(query)
            if result:
                return jsonify(result), 200

            # 3. Try username search as fallback
            result = search_username(query)
            if result:
                return jsonify(result), 200

        # Return result if found in any of the searches
        if result:
            return jsonify(result), 200

        # No matches in threat intelligence database
        return jsonify({
            "error": "No results found",
            "message": f"Aucune donnée trouvée pour '{query}'"
        }), 404

    except Exception as e:
        print(f"Error in threat intel search: {e}")
        return jsonify({"error": "Internal server error"}), 500


@threat_intel_bp.route("/timeline", methods=["POST"])
def timeline() -> Tuple[Response, int]:
    """
    Retrieve timeline data for a specific IP address.

    This endpoint retrieves activity timeline data for a given IP address,
    showing attack patterns over the specified time period.

    Expects JSON body with:
    - ip_address: The IP address to query
    - timeline: Time period ('24h', '7d', or '30d'), defaults to '24h'

    Returns:
        JSON response with timeline data including attack counts by period.
        HTTP status codes: 200 (success), 400 (invalid IP or missing parameter), 500 (error).
    """
    try:
        data = request.get_json()
        ip_address = data.get("ip_address", "").strip()
        timeline_param = data.get("timeline", "24h").strip()

        if not ip_address:
            return jsonify({"error": "IP address parameter is required"}), 400

        # Validate IP format using regex
        if not is_valid_ip(ip_address):
            return jsonify({
                "error": "Invalid IP format",
                "message": f"'{ip_address}' n'est pas une adresse IP valide"
            }), 400

        # Validate timeline parameter against allowed values
        valid_timelines = ["24h", "7d", "30d"]
        if timeline_param not in valid_timelines:
            # Default to 24h if invalid value provided
            timeline_param = "24h"

        # Fetch and aggregate attack timeline data for this IP
        timeline_data = get_ip_timeline(ip_address, timeline_param)

        return jsonify(timeline_data), 200

    except Exception as e:
        print(f"Error in threat intel timeline: {e}")
        return jsonify({"error": "Internal server error"}), 500
