from flask import Flask
from flask_cors import CORS
from config import Config
from db.database import init_db
from routes import register_routes

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {
    "origins": ["https://agent-bot-front.vercel.app"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

init_db(app)
register_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(app.config['PORT']))
