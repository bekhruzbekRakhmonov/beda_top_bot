from flask import Blueprint, request, jsonify
from models.message import Message
from services.auth_service import token_required
from services.chatbot_service import generate_response
from services.nlp_service import get_intent
from db.database import get_session

message_routes = Blueprint('message_routes', __name__)


@message_routes.route('/api/chatbot', methods=['POST'])
@token_required
def handle_chatbot(current_agent):
    data = request.json
    user_message = data.get('message', '')
    context = data.get('context', {})

    # Save user message
    add_message(current_agent.id, user_message, 'agent')

    response, actions = generate_response(user_message, context, current_agent)

    # Save assistant response
    add_message(current_agent.id, response, 'assistant')

    context['last_intent'] = get_intent(user_message)
    context['last_message'] = user_message

    return jsonify({
        'response': response,
        'context': context,
        'actions': actions
    })


@message_routes.route('/api/messages', methods=['POST'])
@token_required
def save_message(current_agent):
    data = request.json
    content = data.get('content')
    sender = data.get('sender')

    if not content or not sender:
        return jsonify({'message': 'Missing content or sender'}), 400

    add_message(current_agent.id, content, sender)

    return jsonify({'message': 'Message saved successfully'}), 201


@message_routes.route('/api/messages', methods=['GET'])
@token_required
def get_messages(current_agent):
    session = get_session()
    messages = session.query(Message).filter_by(
        agent_id=current_agent.id).order_by(Message.timestamp).all()

    return jsonify([{
        'id': m.id,
        'content': m.content,
        'sender': m.sender,
        'timestamp': m.timestamp.isoformat()
    } for m in messages])


def add_message(agent_id, content, sender):
    new_message = Message(
        agent_id=agent_id,
        content=content,
        sender=sender
    )

    session = get_session()
    session.add(new_message)
    session.commit()
