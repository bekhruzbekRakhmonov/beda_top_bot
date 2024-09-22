from flask import Blueprint, request, jsonify
from models.agent import Agent
from services.auth_service import create_token, token_required
from db.database import get_session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

agent_routes = Blueprint('agent_routes', __name__)


@agent_routes.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    session = get_session()
    agent = session.query(Agent).filter_by(email=email).first()

    if agent and check_password_hash(agent.password, password):
        token = create_token(agent.id)
        return jsonify({'token': token, 'agent_name': agent.name})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@agent_routes.route('/api/create_agent', methods=['POST'])
def create_agent():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    agency_id = data.get('agency_id', 1)

    if not all([name, email, password]):
        return jsonify({'message': 'Missing required fields'}), 400

    session = get_session()
    existing_agent = session.query(Agent).filter_by(email=email).first()
    if existing_agent:
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_agent = Agent(
        agent_id=f"AG{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        name=name,
        email=email,
        password=hashed_password,
        agency_id=agency_id
    )

    session.add(new_agent)
    session.commit()

    return jsonify({'message': 'Agent created successfully', 'agent_id': new_agent.agent_id}), 201


@agent_routes.route('/api/agents/me', methods=['GET'])
@token_required
def get_current_agent(current_agent):
    return jsonify({
        'id': current_agent.id,
        'agent_id': current_agent.agent_id,
        'name': current_agent.name,
        'email': current_agent.email,
        'agency_id': current_agent.agency_id
    })
