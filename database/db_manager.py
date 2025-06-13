import psycopg
from psycopg.errors import OperationalError, UniqueViolation, UndefinedTable
from config import Config
from contextlib import contextmanager

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados PostgreSQL usando as configurações do Config.
    Levanta um RuntimeError se a conexão falhar.
    """
    db_config = Config.DATABASE
    try:
        # Tenta conectar ao banco de dados com as credenciais fornecidas.
        conn = psycopg.connect(
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        return conn
    except OperationalError as e:
        # Captura erros de operação (ex: credenciais inválidas, banco não disponível).
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        raise RuntimeError(
            "Não foi possível conectar ao banco de dados. Verifique as configurações e o status do PostgreSQL.") from e
    except Exception as e:
        # Captura quaisquer outros erros inesperados durante a conexão.
        print(f"Erro inesperado ao tentar conectar ao banco de dados: {e}")
        raise RuntimeError("Erro inesperado ao conectar ao banco de dados.") from e


@contextmanager
def get_db_cursor(commit=False):
    """
    Fornece um cursor de banco de dados, garantindo que a conexão seja fechada.
    Se 'commit' for True, a transação é commitada; caso contrário, é revertida em caso de erro.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        yield cursor  # O cursor é retornado para ser usado dentro do bloco 'with'.
        if commit:
            conn.commit()  # Commita as alterações se 'commit' for True.
    except Exception as e:
        if conn:
            conn.rollback()  # Reverte as alterações em caso de erro.
        print(f"Erro na transação do banco de dados: {e}")
        raise  # Re-lança a exceção para que o chamador possa tratá-la.
    finally:
        if cursor:
            cursor.close()  # Garante que o cursor seja fechado.
        if conn:
            conn.close()  # Garante que a conexão seja fechada.


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Executa uma consulta SQL e retorna resultados opcionais.

    Args:
        query (str): A consulta SQL a ser executada.
        params (tuple, optional): Parâmetros para a consulta, para prevenir SQL injection.
        fetchone (bool): Se True, retorna apenas a primeira linha do resultado.
        fetchall (bool): Se True, retorna todas as linhas do resultado.
        commit (bool): Se True, commita a transação após a execução da query.

    Returns:
        mixed: Retorna True em caso de sucesso (sem fetch), a linha (se fetchone),
              todas as linhas (se fetchall), ou False em caso de erro de operação.
              Levanta exceções para erros de unicidade ou outros erros inesperados.
    """
    try:
        with get_db_cursor(commit=commit) as cursor:
            cursor.execute(query, params)
            if fetchone:
                return cursor.fetchone()
            elif fetchall:
                return cursor.fetchall()
            else:
                return True  # Retorna True para operações de inserção/atualização/deleção bem-sucedidas.
    except OperationalError as e:
        print(f"Erro de operação no banco de dados: {e}")
        return False  # Retorna False para erros que impedem a operação (ex: banco offline).
    except UniqueViolation as e:
        print(f"Erro de violação de unicidade: {e}")
        # Re-lança a exceção com uma mensagem mais amigável, útil para validação.
        raise ValueError("Violação de unicidade de dados. Este registro já existe.") from e
    except Exception as e:
        print(f"Erro inesperado ao executar consulta: {e}")
        raise  # Re-lança quaisquer outras exceções inesperadas.


def check_and_update_table_constraints():
    """
    Verifica e atualiza as constraints da tabela 'users'.
    Adiciona colunas 'password_hash', 'is_active', 'is_admin' se elas não existirem.
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            # Verifica a coluna 'password_hash'
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'password_hash';
            """)
            if not cursor.fetchone():
                print("Adicionando coluna 'password_hash' à tabela 'users'...")
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT '';") # Adicionado DEFAULT para evitar problemas em tabelas existentes
                print("Coluna 'password_hash' adicionada à tabela 'users'.")
            else:
                print("Coluna 'password_hash' já existe.")

            # Verifica a coluna 'is_active'
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'is_active';
            """)
            if not cursor.fetchone():
                print("Adicionando coluna 'is_active' à tabela 'users'...")
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;")
                print("Coluna 'is_active' adicionada à tabela 'users'.")
            else:
                print("Coluna 'is_active' já existe.")

            # Verifica a coluna 'is_admin'
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'is_admin';
            """)
            if not cursor.fetchone():
                print("Adicionando coluna 'is_admin' à tabela 'users'...")
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
                print("Coluna 'is_admin' adicionada à tabela 'users'.")
            else:
                print("Coluna 'is_admin' já existe.")

    except UndefinedTable:
        # Este aviso é normal se a tabela 'users' ainda não foi criada por Usuario.create_table().
        print("Aviso: A tabela 'users' não existe ao tentar verificar/atualizar constraints. Isso é normal se 'create_table()' for executado primeiro.")
    except Exception as e:
        print(f"Erro inesperado durante a verificação/correção das constraints: {e}")

