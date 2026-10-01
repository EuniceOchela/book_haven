import os
from dotenv import load_dotenv

load_dotenv(override=True)


db_url = os.getenv("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
     db_url = db_url.replace("postgres://", "postgresql://", 1)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # SQLALCHEMY_DATABASE_URI = "postgresql://postgres:John4u.com@localhost:5432/the_bookers"
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flutterwave
    FLW_PUBLIC_KEY = os.getenv('FLW_PUBLIC_KEY')
    FLW_SECRET_KEY = os.getenv('FLW_SECRET_KEY')
    CLAUDINARY_API_KEY = os.getenv('CLAUDINARY_API_KEY')
    CLAUDINARY_API_SECRET = os.getenv('CLAUDINARY_API_SECRET')
    CLAUDINARY_URL = os.getenv('CLAUDINARY_URL')


    # Email (optional for now)
    MAIL_SERVER = 'smtp.hostinger.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')