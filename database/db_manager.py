# database/db_manager.py

import psycopg
from psycopg.errors import OperationalError, UniqueViolation, UndefinedTable
from config import Config


def open_connection():
    db_config = Config.DATABASE
    try:
        conn = psycopg.connect(
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        return conn
    except OperationalError as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        raise RuntimeError(
            "Não foi possível conectar ao banco de dados. Verifique as configurações e o status do PostgreSQL.") from e
    except Exception as e:
        print(f"Erro inesperado ao tentar conectar ao banco de dados: {e}")
        raise RuntimeError(
            "Erro inesperado ao conectar ao banco de dados.") from e


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False, connection=None, cursor=None):
    _conn = connection
    _cursor = cursor
    close_internally = False

    try:
        if _conn is None:
            _conn = open_connection()
            _cursor = _conn.cursor()
            close_internally = True

        _cursor.execute(query, params)

        result = None
        if fetchone:
            result = _cursor.fetchone()
        elif fetchall:
            result = _cursor.fetchall()
        elif commit and close_internally:
            _conn.commit()
            result = True

        return result if (fetchone or fetchall) else (_cursor.rowcount > 0 if commit else True)

    except OperationalError as e:
        if close_internally and _conn:
            _conn.rollback()
        print(f"Erro de operação no banco de dados: {e}")
        raise
    except UniqueViolation as e:
        if close_internally and _conn:
            _conn.rollback()
        print(f"Erro de violação de unicidade: {e}")
        raise ValueError(
            "Violação de unicidade de dados. Este registro já existe.") from e
    except UndefinedTable as e:
        if close_internally and _conn:
            _conn.rollback()
        print(f"Erro: Tabela não definida: {e}")
        raise RuntimeError(
            "Erro no esquema do banco de dados. Tabela não encontrada.") from e
    except Exception as e:
        if close_internally and _conn:
            _conn.rollback()
        print(f"Erro inesperado ao executar consulta: {e}")
        raise

    finally:
        if close_internally and _cursor:
            _cursor.close()
        if close_internally and _conn:
            _conn.close()
