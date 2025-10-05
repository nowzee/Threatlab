from flask import Blueprint, jsonify
from module.database.detail_log_analyse import get_alert_detail_by_id

alert_details_bp = Blueprint("alert_details_bp", __name__, url_prefix="/log-analyse")

@alert_details_bp.route("/alert/<int:alert_id>", methods=["GET"])
def get_alert_details(alert_id):
    """
    """
    alert_detail = get_alert_detail_by_id(alert_id)

    if alert_detail is None:
        return jsonify({"error": "Alerte introuvable"}), 404

    return jsonify(alert_detail), 200
