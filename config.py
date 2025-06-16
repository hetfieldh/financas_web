# \config.py

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configurações da aplicação Flask.
    As variáveis são carregadas do arquivo .env.
    """
    SECRET_KEY = os.getenv('SECRET_KEY')

    DATABASE = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
