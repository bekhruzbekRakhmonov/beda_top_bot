from flask import Blueprint, request, jsonify
from models.property import Property
from services.auth_service import token_required
from db.database import get_session

property_routes = Blueprint('property_routes', __name__)


@property_routes.route('/api/properties', methods=['GET'])
@token_required
def get_properties(current_agent):
    session = get_session()
    properties = session.query(Property).filter_by(
        agent_id=current_agent.id).all()
    return jsonify([{
        'id': p.id,
        'address': p.address,
        'price': p.price,
        'bedrooms': p.bedrooms,
        'bathrooms': p.bathrooms,
        'square_feet': p.square_feet,
        'description': p.description
    } for p in properties])


@property_routes.route('/api/properties', methods=['POST'])
@token_required
def add_property(current_agent):
    data = request.json
    required_fields = ['address', 'price',
                       'bedrooms', 'bathrooms', 'square_feet']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        new_property = Property(
            address=data['address'],
            price=float(data['price']),
            bedrooms=int(data['bedrooms']),
            bathrooms=int(data['bathrooms']),
            square_feet=float(data['square_feet']),
            description=data.get('description', ''),
            agent_id=current_agent.id
        )

        session = get_session()
        session.add(new_property)
        session.commit()

        property_data = {
            'id': new_property.id,
            'address': new_property.address,
            'price': new_property.price,
            'bedrooms': new_property.bedrooms,
            'bathrooms': new_property.bathrooms,
            'square_feet': new_property.square_feet,
            'description': new_property.description
        }

        return jsonify({'message': 'Property added successfully', 'property': property_data}), 201

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error adding property: {str(e)}'}), 500
