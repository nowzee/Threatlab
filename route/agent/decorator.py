from functools import wraps
from flask import request, current_app, jsonify, g
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

def agent_jwt_required(fn):
    """
    Décorateur : exige un JWT valide contenant 'agent_id' et que l'agent existe.
    Pose l'agent dans flask.g.agent (et g.agent_id).
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 1) Récupérer le token (header Bearer ou champ JSON 'token')
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(None, 1)[1].strip()
        else:
            # fallback : token dans JSON body ou param GET
            try:
                token = (request.get_json(silent=True) or {}).get('token') or request.args.get('token')
            except Exception:
                token = None

        if not token:
            return jsonify({'success': False, 'error': 'Missing authentication token'}), 401

        secret = current_app.config.get('SECRET_KEY')
        if not secret:
            return jsonify({'success': False, 'error': 'Server misconfiguration: SECRET_KEY missing'}), 500

        # 2) Décoder et valider le JWT
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
        except ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'success': False, 'error': f'Token decode error: {str(e)}'}), 401

        # 3) Récupérer agent_id dans le payload
        agent_id = payload.get('agent_id')
        if not agent_id:
            return jsonify({'success': False, 'error': 'Token missing agent_id'}), 401

        # 4) Vérifier existence de l'agent en DB
        agent = get_agent_by_id(agent_id)
        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 401

        # 5) Attacher l'agent à flask.g pour la route
        g.agent_id = agent_id
        g.agent = agent
        g.agent_token_payload = payload

        # Appel de la vue protégée
        return fn(*args, **kwargs)

    return wrapper
