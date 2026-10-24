import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Database host and name come from the environment, never hard-coded, so
    the application can be pointed at a test database (TMA Q2b, Q4b)."""

    MONGODB_SETTINGS = {
        'db': os.getenv('MONGODB_DB', 'skipq'),
        'host': os.getenv('MONGODB_HOST', '127.0.0.1'),
        'port': int(os.getenv('MONGODB_PORT', '27017')),
        'serverSelectionTimeoutMS': int(os.getenv('MONGODB_TIMEOUT_MS', '2000')),
    }
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-not-for-production')
