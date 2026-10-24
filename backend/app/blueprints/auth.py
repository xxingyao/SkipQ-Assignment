from datetime import datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.errors import SkipQError
from app.models.token import UserTokens
from app.models.users import User

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/user')


@auth_bp.route('/gettoken', methods=['POST'])
def gettoken():
    data = request.get_json(silent=True) or request.form
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        raise SkipQError('Email and password are both required')

    user = User.getUser(email=email)
    if not user or not check_password_hash(user.password, password):
        # One message for both failures, so a registered address cannot be
        # identified by comparing responses.
        return jsonify({'error': 'Invalid email or password'}), 401

    record = UserTokens.getToken(email=email)
    if not record:
        stamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        record = UserTokens.createToken(
            email=email, token=generate_password_hash(email + stamp))

    return jsonify({'token': record.token,
                    'role': user.role,
                    'name': user.name}), 200