"""Read-only platform configuration exposed to the authenticated frontend."""
from typing import Tuple

from flask import Blueprint, jsonify, Response

from module.config.app_settings import (
    get_timezone_name,
    current_utc_offset,
    list_timezones,
)

config_system_bp = Blueprint('config_system', __name__, url_prefix='/api/config')


@config_system_bp.route('/timezone', methods=['GET'])
def get_timezone() -> Tuple[Response, int]:
    """Return the configured display timezone and its current UTC offset."""
    return jsonify({
        'timezone': get_timezone_name(),
        'offset': current_utc_offset(),
    }), 200


@config_system_bp.route('/timezones', methods=['GET'])
def get_timezones() -> Tuple[Response, int]:
    """Return the list of selectable IANA timezone names (common ones first)."""
    return jsonify({'timezones': list_timezones()}), 200
