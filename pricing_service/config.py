# FILE: pricing_service/config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Konfigurasi Dasar"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    SECRET_KEY = os.getenv('SECRET_KEY_PRICING', 'price_secret') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False