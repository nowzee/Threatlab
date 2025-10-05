from flask import Blueprint, jsonify, Response
from module.database.agent import get_default_metric_data, get_agent_details, get_country_ranking, get_complete_report_data, get_password_ranking
from datetime import datetime
import os, traceback
from jinja2 import Template

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')


@agent_user_api_bp.route("/metric_dashboard", methods=['GET'])
def get_default_metric_data_agent():

    data = get_default_metric_data()

    return jsonify(data)


@agent_user_api_bp.route("/new_logs", methods=['GET'])
def get_new_logs_agent():

    data = get_agent_details()

    return jsonify(data)


@agent_user_api_bp.route("/country_ranking", methods=['GET'])
def get_country_ranking_data():

    data = get_country_ranking()

    return jsonify(data)

@agent_user_api_bp.route("/password_ranking", methods=['GET'])
def get_password_ranking_data():

    data = get_password_ranking()

    return jsonify(data)


@agent_user_api_bp.route("/generated_rapport", methods=['GET'])
def generate_rapport():
    try:
        report_data = get_complete_report_data()
        generation_date = datetime.now().strftime('%d/%m/%Y à %H:%M')

        # Calculate percentages for countries
        total_attacks = sum(item['attack_count'] for item in report_data['country_ranking'])
        for country in report_data['country_ranking']:
            percentage = round((country['attack_count'] / total_attacks * 100), 2) if total_attacks > 0 else 0
            country['percentage'] = f"{percentage}%"

        # Read CSS file
        css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'templates', 'rapport.css')
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        except UnicodeDecodeError:
            with open(css_path, 'r', encoding='latin-1') as f:
                css_content = f.read()

        context = {
            'generation_date': generation_date,
            'period': '30 derniers jours',
            'css_content': css_content,

            # Metrics
            'total_ips': report_data['metrics']['ip_count'],
            'total_attacks': report_data['metrics']['tentative_access'],
            'active_agents': report_data['metrics']['active_honeypot'],
            'payloads_collected': report_data['metrics']['Sample_downloaded'],

            # Data tables
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

        # Generate HTML from template
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'templates', 'template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except UnicodeDecodeError:
            with open(template_path, 'r', encoding='latin-1') as f:
                template_content = f.read()

        template = Template(template_content)
        html = template.render(**context)
        filename = f"ThreatLabs_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        response = Response(html, mimetype='text/html')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/html; charset=utf-8'

        return response

    except Exception as e:
        print(f"Error generating report: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate report'}), 500