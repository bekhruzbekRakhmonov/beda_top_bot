from flask import Blueprint, request, jsonify
from models.client import Client
from services.auth_service import token_required
from db.database import get_session

client_routes = Blueprint('client_routes', __name__)


@client_routes.route('/api/clients', methods=['GET'])
@token_required
def get_clients(current_agent):
    session = get_session()
    clients = session.query(Client).filter_by(agent_id=current_agent.id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone
    } for c in clients])


@client_routes.route('/api/clients', methods=['POST'])
@token_required
def add_client(current_agent):
    data = request.json
    required_fields = ['name', 'email', 'phone']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        new_client = Client(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            agent_id=current_agent.id
        )

        session = get_session()
        session.add(new_client)
        session.commit()

        client_data = {
            'id': new_client.id,
            'name': new_client.name,
            'email': new_client.email,
            'phone': new_client.phone
        }

        return jsonify({'message': 'Client added successfully', 'client': client_data}), 201

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error adding client: {str(e)}'}), 500
