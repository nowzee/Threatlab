from module.database.db_manager import DatabaseManagerHoneypot

def last_log_analyse(timeline):
    global interval

    if timeline == '24h':
        interval = "-1 day"
    elif timeline == '7d':
        interval = "-7 day"
    elif timeline == '30d':
        interval = "-30 day"

    with DatabaseManagerHoneypot() as db:
        db.execute("SELECT created_at, country_code, country_name, agent_id  "
                   "FROM attack_logs WHERE created_at >= datetime('now', ?) ORDER BY created_at DESC", (interval,))
        result = db.fetchall()
        if not result:
            return False

        return result