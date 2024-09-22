import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import jwt as pyjwt
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {
    "origins": ["https://agent-bot-front.vercel.app"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Use environment variable for database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///real_estate.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Set up the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# JWT Secret Key
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")

# Models


class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    agency_id = Column(Integer, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    clients = relationship("Client", back_populates="agent")
    properties = relationship("Property", back_populates="agent")
    messages = relationship("Message", back_populates="agent")


class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    square_feet = Column(Float, nullable=False)
    description = Column(Text)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    agent = relationship("Agent", back_populates="properties")


class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    agent = relationship("Agent", back_populates="clients")


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    content = Column(Text, nullable=False)
    sender = Column(String, nullable=False)  # 'agent' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="messages")


# Add this to the Agent model
messages = relationship("Message", back_populates="agent")

Base.metadata.create_all(engine)

# NLP helpers
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    return [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]


def get_intent(text):
    preprocessed = preprocess_text(text)
    if any(word in preprocessed for word in ['document', 'prepare', 'contract']):
        return 'prepare_document'
    elif any(word in preprocessed for word in ['onboard', 'new', 'client']):
        return 'client_onboarding'
    elif any(word in preprocessed for word in ['search', 'find', 'property']):
        return 'property_search'
    elif any(word in preprocessed for word in ['market', 'analysis', 'trend']):
        return 'market_analysis'
    elif any(word in preprocessed for word in ['client', 'info', 'information']):
        return 'client_info'
    else:
        return 'general_query'

# Authentication decorator


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            session = Session()
            current_agent = session.query(Agent).filter_by(
                id=data['agent_id']).first()
            session.close()
            if not current_agent:
                raise ValueError('Agent not found')
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_agent, *args, **kwargs)
    return decorated

# Chatbot helper functions


def generate_response(message, context, agent):
    intent = get_intent(message)
    model = genai.GenerativeModel('gemini-pro')

    session = Session()
    clients = session.query(Client).filter_by(agent_id=agent.id).all()
    client_info = [
        f"{c.name} (Email: {c.email}, Phone: {c.phone})" for c in clients]

    # Retrieve recent messages
    recent_messages = session.query(Message).filter_by(
        agent_id=agent.id).order_by(Message.timestamp.desc()).limit(10).all()
    recent_messages.reverse()  # Oldest first

    # Map 'agent' to 'user' and 'assistant' to 'model'
    chat_history = [{"role": "user" if m.sender == "agent" else "model", "parts": [m.content]}
                    for m in recent_messages]
    chat = model.start_chat(history=chat_history)

    session.close()

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

# API Routes


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    session = Session()
    agent = session.query(Agent).filter_by(email=email).first()
    session.close()

    if agent and check_password_hash(agent.password, password):
        token = pyjwt.encode({
            'agent_id': agent.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({'token': token, 'agent_name': agent.name})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/api/create_agent', methods=['POST'])
def create_agent():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    agency_id = data.get('agency_id', 1)

    if not all([name, email, password]):
        return jsonify({'message': 'Missing required fields'}), 400

    session = Session()
    existing_agent = session.query(Agent).filter_by(email=email).first()
    if existing_agent:
        session.close()
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
    session.close()

    return jsonify({'message': 'Agent created successfully', 'agent_id': new_agent.agent_id}), 201


@app.route('/api/chatbot', methods=['POST'])
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


def add_message(agent_id, content, sender):
    new_message = Message(
        agent_id=agent_id,
        content=content,
        sender=sender
    )

    session = Session()
    session.add(new_message)
    session.commit()
    session.close()


@app.route('/api/properties', methods=['GET'])
@token_required
def get_properties(current_agent):
    session = Session()
    properties = session.query(Property).filter_by(
        agent_id=current_agent.id).all()
    session.close()
    return jsonify([{
        'id': p.id,
        'address': p.address,
        'price': p.price,
        'bedrooms': p.bedrooms,
        'bathrooms': p.bathrooms,
        'square_feet': p.square_feet,
        'description': p.description
    } for p in properties])


@app.route('/api/properties', methods=['POST'])
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

        session = Session()
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

        session.close()
        return jsonify({'message': 'Property added successfully', 'property': property_data}), 201

    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({'message': f'Error adding property: {str(e)}'}), 500


@app.route('/api/clients', methods=['GET'])
@token_required
def get_clients(current_agent):
    session = Session()
    clients = session.query(Client).filter_by(agent_id=current_agent.id).all()
    session.close()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone
    } for c in clients])


@app.route('/api/clients', methods=['POST'])
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

        session = Session()
        session.add(new_client)
        session.commit()

        client_data = {
            'id': new_client.id,
            'name': new_client.name,
            'email': new_client.email,
            'phone': new_client.phone
        }

        session.close()
        return jsonify({'message': 'Client added successfully', 'client': client_data}), 201

    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({'message': f'Error adding client: {str(e)}'}), 500


@app.route('/api/agents/me', methods=['GET'])
@token_required
def get_current_agent(current_agent):
    return jsonify({
        'id': current_agent.id,
        'agent_id': current_agent.agent_id,
        'name': current_agent.name,
        'email': current_agent.email,
        'agency_id': current_agent.agency_id
    })


@app.route('/api/messages', methods=['POST'])
@token_required
def save_message(current_agent):
    data = request.json
    content = data.get('content')
    sender = data.get('sender')

    if not content or not sender:
        return jsonify({'message': 'Missing content or sender'}), 400

    new_message = Message(
        agent_id=current_agent.id,
        content=content,
        sender=sender
    )

    session = Session()
    session.add(new_message)
    session.commit()
    session.close()

    return jsonify({'message': 'Message saved successfully'}), 201


@app.route('/api/messages', methods=['GET'])
@token_required
def get_messages(current_agent):
    session = Session()
    messages = session.query(Message).filter_by(
        agent_id=current_agent.id).order_by(Message.timestamp).all()
    session.close()

    return jsonify([{
        'id': m.id,
        'content': m.content,
        'sender': m.sender,
        'timestamp': m.timestamp.isoformat()
    } for m in messages])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
