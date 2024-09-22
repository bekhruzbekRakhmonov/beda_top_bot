from flask import request, jsonify, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta
from models.agent import Agent
from db.database import get_session


def create_token(agent_id):
    return jwt.encode({
        'agent_id': agent_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(
                token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            session = get_session()
            current_agent = session.query(Agent).filter_by(
                id=data['agent_id']).first()
            if not current_agent:
                raise ValueError('Agent not found')
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_agent, *args, **kwargs)
    return decorated
