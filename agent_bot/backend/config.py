import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///real_estate.db")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    PORT = int(os.getenv('PORT', 5000))

    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in environment variables")
