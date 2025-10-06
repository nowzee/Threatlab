"""
Agent User API Route Module.

This module provides Flask routes for retrieving agent metrics, logs,
rankings, and generating reports for the user dashboard.
"""

from typing import Tuple
from flask import Blueprint, jsonify, Response
from module.database.agent import get_default_metric_data, get_agent_details, get_country_ranking, get_complete_report_data, get_password_ranking
from datetime import datetime
import os
import traceback
from jinja2 import Template

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')


@agent_user_api_bp.route("/metric_dashboard", methods=['GET'])
def get_default_metric_data_agent() -> Response:
    """
    Retrieve default dashboard metrics.

    Returns:
        JSON response with dashboard metrics including IP count,
        attack attempts, active honeypots, and samples downloaded.
    """
    data = get_default_metric_data()

    return jsonify(data)


@agent_user_api_bp.route("/new_logs", methods=['GET'])
def get_new_logs_agent() -> Response:
    """
    Retrieve recent logs and agent details.

    Returns:
        JSON response with agent activity logs and details.
    """
    data = get_agent_details()

    return jsonify(data)


@agent_user_api_bp.route("/country_ranking", methods=['GET'])
def get_country_ranking_data() -> Response:
    """
    Retrieve country-based attack ranking statistics.

    Returns:
        JSON response with countries ranked by attack frequency.
    """
    data = get_country_ranking()

    return jsonify(data)


@agent_user_api_bp.route("/password_ranking", methods=['GET'])
def get_password_ranking_data() -> Response:
    """
    Retrieve most commonly attempted passwords.

    Returns:
        JSON response with password ranking statistics.
    """
    data = get_password_ranking()

    return jsonify(data)


@agent_user_api_bp.route("/generated_rapport", methods=['GET'])
def generate_rapport() -> Tuple[Response, int]:
    """
    Generate a complete HTML report with attack statistics and analysis.

    This endpoint collects comprehensive data from the database including
    metrics, country rankings, password statistics, and agent details,
    then generates an HTML report file for download.

    Returns:
        An HTML file as download with complete threat intelligence report,
        or JSON error response on failure.
        HTTP status codes: 200 (success), 500 (generation error).
    """
    try:
        # Fetch all required data from database for comprehensive report
        report_data = get_complete_report_data()
        generation_date = datetime.now().strftime('%d/%m/%Y à %H:%M')

        # Calculate percentage distribution for country attacks
        total_attacks = sum(item['attack_count'] for item in report_data['country_ranking'])
        for country in report_data['country_ranking']:
            # Compute percentage of total attacks for each country
            percentage = round((country['attack_count'] / total_attacks * 100), 2) if total_attacks > 0 else 0
            country['percentage'] = f"{percentage}%"

        # Load CSS stylesheet for HTML report styling
        css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'templates', 'rapport.css')
        try:
            # Try UTF-8 encoding first
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            with open(css_path, 'r', encoding='latin-1') as f:
                css_content = f.read()

        # Build context dictionary with all data for Jinja2 template
        context = {
            'generation_date': generation_date,
            'period': '30 derniers jours',
            'css_content': css_content,

            # High-level metrics for executive summary
            'total_ips': report_data['metrics']['ip_count'],
            'total_attacks': report_data['metrics']['tentative_access'],
            'active_agents': report_data['metrics']['active_honeypot'],
            'payloads_collected': report_data['metrics']['Sample_downloaded'],

            # Detailed analysis tables (limit to top N for readability)
            'top_countries': report_data['country_ranking'][:10],
            'top_passwords': report_data['top_passwords'][:15],
            'top_usernames': report_data['top_usernames'][:15],
            'top_ips': report_data['top_ips'][:15],
            'agents': report_data['agents'],
            'payloads': report_data['payloads'],
            'port_distribution': report_data['port_distribution'],
            'credential_combinations': report_data['credential_combinations'][:10],
            'service_distribution': report_data['service_distribution'],
        }

        # Load HTML template and render with report data
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'templates', 'template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except UnicodeDecodeError:
            with open(template_path, 'r', encoding='latin-1') as f:
                template_content = f.read()

        # Render template with Jinja2
        template = Template(template_content)
        html = template.render(**context)
        # Generate timestamped filename for download
        filename = f"ThreatLabs_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # Create response with proper headers for file download
        response = Response(html, mimetype='text/html')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/html; charset=utf-8'

        return response

    except Exception as e:
        print(f"Error generating report: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report'}), 500