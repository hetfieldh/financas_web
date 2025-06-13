import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """
    Configurações da aplicação Flask.
    As variáveis são carregadas do arquivo .env.
    """
    # Chave secreta usada para segurança de sessão e outras funcionalidades do Flask.
    # É crucial que esta chave seja complexa e mantida em segredo.
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Dicionário com as configurações de conexão do banco de dados PostgreSQL.
    DATABASE = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }

