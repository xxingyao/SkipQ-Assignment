from functools import wraps

from flask import jsonify
from flask_httpauth import HTTPBasicAuth

from app.models.errors import NotPermitted
from app.models.token import UserTokens
from app.models.users import User

token_auth = HTTPBasicAuth()


@token_auth.verify_password
def verify_token(email, token):
    """Returns the User rather than True, so current_user() carries the
    identity the role and scope checks need. The lab returned a bare boolean,
    which is why it could do neither."""
    if not email or not token:
        return None
    stored = UserTokens.getToken(email=email)
    if not stored or stored.token != token:
        return None
    return User.getUser(email=email)


@token_auth.error_handler
def auth_error(status):
    return jsonify({'error': 'A valid email and token are required'}), 401


def current_user():
    return token_auth.current_user()


def role_required(*roles):
    """The ROLE CHECK. Declared once per Blueprint rather than per view."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None or user.role not in roles:
                raise NotPermitted(
                    'This endpoint is for %s accounts only'
                    % ' or '.join(r.lower() for r in roles))
            return view(*args, **kwargs)
        return wrapper
    return decorator
