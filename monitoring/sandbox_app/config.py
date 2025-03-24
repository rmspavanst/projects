# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '1234qwerty')  # A secret key for security
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@192.168.0.238/sandbox_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False