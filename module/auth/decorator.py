"""
Authentication Decorator Module.

This module provides Flask decorators for protecting routes that require
JWT-based agent authentication.
"""

from functools import wraps
from typing import Callable, Any, Tuple
from flask import request, current_app, jsonify, g, Response
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


def agent_jwt_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator requiring a valid JWT containing 'agent_id'.

    This decorator validates JWT tokens for agent authentication and stores
    the agent information in Flask's g object for use in the protected route.

    The token can be provided in three ways:
    1. Authorization header: "Bearer <token>"
    2. JSON body field: {"token": "<token>"}
    3. Query parameter: ?token=<token>

    Args:
        fn: The Flask route function to protect.

    Returns:
        The wrapped function that performs JWT validation before execution.

    Notes:
        Sets g.agent_id and g.agent_token_payload on successful authentication.
    """
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Tuple[Response, int]:
        # 1) Get the token (Bearer header or JSON field 'token')
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header.split(None, 1)[1].strip()
        else:
            # fallback: token in JSON body or GET param
            try:
                token = (request.get_json(silent=True) or {}).get('token') or request.args.get('token')
            except Exception:
                token = None

        if not token:
            return jsonify({'success': False, 'error': 'Missing authentication token'}), 401

        secret = current_app.config.get('SECRET_KEY')
        if not secret:
            return jsonify({'success': False, 'error': 'Server misconfiguration: SECRET_KEY missing'}), 500

        # 2) Decode and validate the JWT
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
        except ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'success': False, 'error': f'Token decode error: {str(e)}'}), 401

        # 3) Get agent_id from the payload
        agent_id = payload.get('agent_id')
        if not agent_id:
            return jsonify({'success': False, 'error': 'Token missing agent_id'}), 401

        # 4) Verify agent existence in DB (currently commented out)
        '''        agent = get_agent_by_id(agent_id)
                if not agent:
                    return jsonify({'success': False, 'error': 'Agent not found'}), 401'''

        # 5) Attach agent to flask.g for the route
        g.agent_id = agent_id
        g.agent_token_payload = payload

        # Call the protected view
        return fn(*args, **kwargs)

    return wrapper
