from flask import Blueprint, jsonify, request
from module.database.threat_intelligence import search_ip, search_password, search_username, is_valid_ip, get_ip_timeline

threat_intel_bp = Blueprint("threat_intel_bp", __name__, url_prefix="/api/threat-intel")


@threat_intel_bp.route("/search", methods=["POST"])
def search():
    """
    Endpoint de recherche unifié pour IP, password ou username
    Peut détecter automatiquement le type ou utiliser le type spécifié
    """
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        search_type = data.get("type", "auto").strip()

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        result = None

        # Si type spécifié, rechercher directement selon le type
        if search_type == "ip":
            if not is_valid_ip(query):
                return jsonify({
                    "error": "Invalid IP format",
                    "message": f"'{query}' n'est pas une adresse IP valide"
                }), 400
            result = search_ip(query)
        elif search_type == "password":
            result = search_password(query)
        elif search_type == "username":
            result = search_username(query)
        else:
            # Mode auto : détection automatique du type
            # 1. Vérifier si c'est une IP valide
            if is_valid_ip(query):
                result = search_ip(query)
                if result:
                    return jsonify(result), 200

            # 2. Chercher dans les passwords
            result = search_password(query)
            if result:
                return jsonify(result), 200

            # 3. Chercher dans les usernames
            result = search_username(query)
            if result:
                return jsonify(result), 200

        # Si un résultat a été trouvé, le retourner
        if result:
            return jsonify(result), 200

        # Aucun résultat trouvé
        return jsonify({
            "error": "No results found",
            "message": f"Aucune donnée trouvée pour '{query}'"
        }), 404

    except Exception as e:
        print(f"Error in threat intel search: {e}")
        return jsonify({"error": "Internal server error"}), 500


@threat_intel_bp.route("/timeline", methods=["POST"])
def timeline():
    """
    Endpoint pour récupérer la timeline d'une IP spécifique
    """
    try:
        data = request.get_json()
        ip_address = data.get("ip_address", "").strip()
        timeline = data.get("timeline", "24h").strip()

        if not ip_address:
            return jsonify({"error": "IP address parameter is required"}), 400

        if not is_valid_ip(ip_address):
            return jsonify({
                "error": "Invalid IP format",
                "message": f"'{ip_address}' n'est pas une adresse IP valide"
            }), 400

        # Valider le paramètre timeline
        valid_timelines = ["24h", "7d", "30d"]
        if timeline not in valid_timelines:
            timeline = "24h"

        # Récupérer les données de la timeline
        timeline_data = get_ip_timeline(ip_address, timeline)

        return jsonify(timeline_data), 200

    except Exception as e:
        print(f"Error in threat intel timeline: {e}")
        return jsonify({"error": "Internal server error"}), 500
