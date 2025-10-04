from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from collections import Counter
from module.database.detail_log_analyse import last_log_analyse

log_analyse_bp = Blueprint("log_analyse_bp", __name__, url_prefix="/log-analyse")

@log_analyse_bp.route("/get_data", methods=["POST"])
def get_data():
    req_data = request.get_json()
    timeline = req_data.get("time", "24h")

    # Récupère les logs depuis la base pour la timeline demandée
    logs = last_log_analyse(timeline)

    # Traitement des logs pour créer la timeline
    data = []
    now = datetime.now()

    # Compter le nombre de logs par période (heure pour 24h, jour pour 7d/30d)
    period_counts = Counter()

    if logs:
        for log in logs:
            try:
                # Le timestamp est le premier élément du tuple
                created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    created_at = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

            # Grouper par heure pour 24h, par jour pour 7d et 30d
            if timeline == "24h":
                period_key = created_at.replace(minute=0, second=0, microsecond=0)
            else:  # 7d ou 30d
                period_key = created_at.replace(hour=0, minute=0, second=0, microsecond=0)

            period_counts[period_key] += 1

    # Générer la timeline complète avec des zéros pour les périodes sans logs
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
