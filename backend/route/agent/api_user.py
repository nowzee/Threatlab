"""
Agent User API Route Module.

This module provides Flask routes for retrieving agent metrics, logs,
rankings, and generating reports for the user dashboard.
"""

from typing import Tuple
from flask import Blueprint, jsonify, Response, request, send_file
from module.database.agent import get_default_metric_data, get_agent_details, get_country_ranking, get_complete_report_data, get_password_ranking, get_top_passwords, get_top_usernames, get_credential_combinations, get_wordlist_stats, get_uploaded_files_page, get_uploaded_file, get_shell_commands_page
from module.auth.session_helpers import is_admin, current_user_id
from module.database.detail_log_analyse import get_db_now
from datetime import datetime
import os
import traceback
from jinja2 import Template

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')


def _scope_owner():
    """None for admins (platform-wide view), the user id for members (own data only)."""
    return None if is_admin() else current_user_id()


@agent_user_api_bp.route("/metric_dashboard", methods=['GET'])
def get_default_metric_data_agent() -> Response:
    """
    Retrieve default dashboard metrics.

    Returns:
        JSON response with dashboard metrics including IP count,
        attack attempts, active honeypots, and samples downloaded.
    """
    data = get_default_metric_data(_scope_owner())

    return jsonify(data)


@agent_user_api_bp.route("/new_logs", methods=['GET'])
def get_new_logs_agent() -> Response:
    """
    Retrieve recent logs and agent details.

    Returns:
        JSON response with agent activity logs and details.
    """
    data = get_agent_details(_scope_owner())

    return jsonify(data)


@agent_user_api_bp.route("/country_ranking", methods=['GET'])
def get_country_ranking_data() -> Response:
    """
    Retrieve country-based attack ranking statistics.

    Returns:
        JSON response with countries ranked by attack frequency.
    """
    data = get_country_ranking(_scope_owner())

    return jsonify(data)


@agent_user_api_bp.route("/password_ranking", methods=['GET'])
def get_password_ranking_data() -> Response:
    """
    Retrieve most commonly attempted passwords.

    Returns:
        JSON response with password ranking statistics.
    """
    data = get_password_ranking(_scope_owner())

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
        now = get_db_now()
        generation_date = now.strftime('%d/%m/%Y à %H:%M')

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
            'active_agents': report_data['metrics']['number_honeypot'],
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
        filename = f"ThreatLabs_Report_{now.strftime('%Y%m%d_%H%M%S')}.html"

        # Create response with proper headers for file download
        response = Response(html, mimetype='text/html')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/html; charset=utf-8'

        return response

    except Exception as e:
        print(f"Error generating report: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report'}), 500


@agent_user_api_bp.route("/wordlists", methods=['GET'])
def get_wordlists_stats() -> Response:
    """
    Get wordlist statistics: counts of passwords, usernames, and combinations.

    Returns:
        JSON with stats and top entries for preview.
    """
    try:
        stats = get_wordlist_stats()
        passwords_top = get_top_passwords(10)
        usernames_top = get_top_usernames(10)
        combos_top = get_credential_combinations()

        return jsonify({
            'passwords': {
                'count': stats['password_count'],
                'total_attempts': stats['password_attempts'],
                'top': passwords_top
            },
            'usernames': {
                'count': stats['username_count'],
                'total_attempts': stats['username_attempts'],
                'top': usernames_top
            },
            'combinations': {
                'count': stats['combo_count'],
                'total_attempts': stats['combo_attempts'],
                'top': combos_top
            }
        })
    except Exception as e:
        print(f"Error getting wordlists: {e}")
        return jsonify({'error': 'Failed to get wordlist stats'}), 500


@agent_user_api_bp.route("/wordlists/download/<wordlist_type>", methods=['GET'])
def download_wordlist(wordlist_type: str) -> Tuple[Response, int]:
    """
    Download a wordlist as a text file.

    Args:
        wordlist_type: 'passwords', 'usernames', or 'combinations'

    Returns:
        A text file download.
    """
    try:
        timestamp = get_db_now().strftime('%Y%m%d_%H%M%S')

        if wordlist_type == 'passwords':
            data = get_top_passwords(None)
            lines = [entry['password'] for entry in data if entry.get('password')]
            filename = f"threatlab_passwords_{timestamp}.txt"

        elif wordlist_type == 'usernames':
            data = get_top_usernames(None)
            lines = [entry['username'] for entry in data if entry.get('username')]
            filename = f"threatlab_usernames_{timestamp}.txt"

        elif wordlist_type == 'combinations':
            data = get_credential_combinations(None)
            lines = [f"{entry['username']}:{entry['password']}" for entry in data
                     if entry.get('username') and entry.get('password')]
            filename = f"threatlab_credentials_{timestamp}.txt"

        elif wordlist_type == 'passwords-ranked':
            data = get_top_passwords(None)
            lines = [f"{entry['password']}\t{entry['count']}" for entry in data if entry.get('password')]
            filename = f"threatlab_passwords_ranked_{timestamp}.csv"

        elif wordlist_type == 'usernames-ranked':
            data = get_top_usernames(None)
            lines = [f"{entry['username']}\t{entry['count']}" for entry in data if entry.get('username')]
            filename = f"threatlab_usernames_ranked_{timestamp}.csv"

        else:
            return jsonify({'error': 'Invalid wordlist type'}), 400

        content = '\n'.join(lines) + '\n'

        response = Response(content, mimetype='text/plain')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'

        return response, 200

    except Exception as e:
        print(f"Error downloading wordlist: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate wordlist'}), 500


@agent_user_api_bp.route("/payloads", methods=['GET'])
def list_payloads() -> Tuple[Response, int]:
    """Paginated list of captured files. ?page=&limit=&q=<search in metadata/content>"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        q = (request.args.get('q') or '').strip() or None
        return jsonify(get_uploaded_files_page(page, limit, q)), 200
    except Exception as e:
        print(f"Error listing payloads: {e}")
        return jsonify({'error': 'Failed to list payloads'}), 500


@agent_user_api_bp.route("/payloads/download/<file_hash>", methods=['GET'])
def download_payload(file_hash: str) -> Tuple[Response, int]:
    """Download a captured binary by its hash."""
    try:
        row = get_uploaded_file(file_hash)
        if not row or not row.get('stored_path') or not os.path.exists(row['stored_path']):
            return jsonify({'error': 'Payload not found'}), 404
        return send_file(row['stored_path'], as_attachment=True,
                         download_name=row.get('file_name') or file_hash)
    except Exception as e:
        print(f"Error downloading payload: {e}")
        return jsonify({'error': 'Failed to download payload'}), 500


@agent_user_api_bp.route("/commands", methods=['GET'])
def list_commands() -> Tuple[Response, int]:
    """Paginated shell commands. ?status=all|success|failed&page=&limit=&q=<search>"""
    try:
        status = request.args.get('status', 'all')
        if status not in ('all', 'success', 'failed'):
            status = 'all'
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        q = (request.args.get('q') or '').strip() or None
        return jsonify(get_shell_commands_page(status, page, limit, q)), 200
    except Exception as e:
        print(f"Error listing commands: {e}")
        return jsonify({'error': 'Failed to list commands'}), 500