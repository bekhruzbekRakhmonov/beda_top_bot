from .agent_routes import agent_routes
from .property_routes import property_routes
from .client_routes import client_routes
from .message_routes import message_routes


def register_routes(app):
    app.register_blueprint(agent_routes)
    app.register_blueprint(property_routes)
    app.register_blueprint(client_routes)
    app.register_blueprint(message_routes)
