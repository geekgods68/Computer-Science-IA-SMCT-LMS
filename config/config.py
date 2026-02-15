import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    DATABASE_URI = os.getenv('DATABASE_URI', 'users.db')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    ENV = os.getenv('ENV', 'development')

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'

config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig
)
