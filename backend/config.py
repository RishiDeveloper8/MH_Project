import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = f"sqlite:///{os.path.join(BASE_DIR, 'finai.db')}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-please-change')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', DEFAULT_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
