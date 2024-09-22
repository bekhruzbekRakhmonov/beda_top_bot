from flask import current_app
import google.generativeai as genai
from models.client import Client
from models.message import Message
from db.database import get_session
from .nlp_service import get_intent


def generate_response(message, context, agent):
    intent = get_intent(message)
    model = genai.GenerativeModel('gemini-pro')

    session = get_session()
    clients = session.query(Client).filter_by(agent_id=agent.id).all()
    client_info = [
        f"{c.name} (Email: {c.email}, Phone: {c.phone})" for c in clients]

    recent_messages = session.query(Message).filter_by(
        agent_id=agent.id).order_by(Message.timestamp.desc()).limit(10).all()
    recent_messages.reverse()

    chat_history = [{"role": "user" if m.sender == "agent" else "model", "parts": [m.content]}
                    for m in recent_messages]
    chat = model.start_chat(history=chat_history)

    prompt = f"""
    You are an AI assistant for Beda Top real estate chatbot and your name is Beda Top. You are currently assisting Agent {agent.name} (ID: {agent.agent_id}).

    Agent's clients:
    {', '.join(client_info)}

    Your task is to help the agent with:
    1. Preparing legal documents for clients
    2. Client onboarding
    3. Property searches
    4. Market analysis
    5. Providing client information
    6. General real estate queries

    Current context: {context}
    Detected intent: {intent}

    User message: {message}

    Please provide a helpful and professional response. If any specific actions are required, include them in your response.
    When discussing clients, use the information provided about the agent's clients.
    """

    response = chat.send_message(prompt)

    actions = []
    if 'prepare a document' in response.text.lower():
        actions.append('prepare_document')
    if 'search for properties' in response.text.lower():
        actions.append('property_search')

    return response.text, actions
