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
        # extract token from three possible locations
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.lower().startswith('bearer '):
            # Extract token from "Bearer <token>" format
            token = auth_header.split(None, 1)[1].strip()
        else:
            # Fallback: check JSON body or GET parameter
            try:
                token = (request.get_json(silent=True) or {}).get('token') or request.args.get('token')
            except Exception:
                token = None

        if not token:
            return jsonify({'success': False, 'error': 'Missing authentication token'}), 401

        # Retrieve agent secret key for JWT validation (separate from user sessions)
        secret = current_app.config.get('AGENT_SECRET_KEY')
        if not secret:
            return jsonify({'success': False, 'error': 'Server misconfiguration: AGENT_SECRET_KEY missing'}), 500

        # Decode and validate JWT signature and structure
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
        except ExpiredSignatureError:
            # Token has exceeded its validity period
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except InvalidTokenError:
            # Token signature invalid or malformed
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        except Exception as e:
            # Catch-all for other decode errors
            return jsonify({'success': False, 'error': f'Token decode error: {str(e)}'}), 401

        # Extract agent_id from payload and verify it exists
        agent_id = payload.get('agent_id')
        if not agent_id:
            return jsonify({'success': False, 'error': 'Token missing agent_id'}), 401

        # Database verification disabled, just for test haah
        '''        agent = get_agent_by_id(agent_id)
                if not agent:
                    return jsonify({'success': False, 'error': 'Agent not found'}), 401'''

        # Store agent info in Flask g object for access in route handlers
        g.agent_id = agent_id
        g.agent_token_payload = payload

        # Execute the protected route with authenticated context
        return fn(*args, **kwargs)

    return wrapper
