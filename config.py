import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = True

# Add other configurations such as SQLALCHEMY_DATABASE_URI if using a database
