from database.db_manager import execute_query
from psycopg.errors import UniqueViolation
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Usuario(UserMixin):
    """
    Representa um usuário no sistema, estendendo UserMixin para integração com Flask-Login.
    """
    def __init__(self, id, name, email, login, password_hash=None, is_admin=False, is_active=True):
        self.id = id
        self.name = name
        self.email = email
        self.login = login
        self.password_hash = password_hash
        self.is_admin = is_admin
        self._is_active = is_active # Propriedade interna para Flask-Login

    def get_id(self):
        """
        Retorna o ID único do usuário como string, necessário para Flask-Login.
        """
        return str(self.id)

    @property
    def is_active(self):
        """
        Retorna True se o usuário está ativo, False caso contrário.
        Necessário para Flask-Login.
        """
        return self._is_active

    @property
    def is_authenticated(self):
        """
        Retorna True se o usuário está autenticado. Sempre True para usuários carregados do DB.
        Necessário para Flask-Login.
        """
        return True

    @property
    def is_anonymous(self):
        """
        Retorna False para usuários reais.
        Necessário para Flask-Login.
        """
        return False

    def set_password(self, password):
        """
        Gera e armazena o hash da senha do usuário.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.
        """
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_table():
        """
        Cria a tabela 'users' no banco de dados se ela ainda não existir.
        Inclui colunas para ID, nome, email, login, hash da senha, e status de administrador/ativo.
        """
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            login VARCHAR(80) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'users' verificada/criada com sucesso.")
        except Exception as e:
            # Erro crítico ao criar a tabela. A aplicação não pode continuar sem ela.
            print(f"ERRO CRÍTICO ao criar/verificar tabela 'users': {e}")
            raise # Re-lança a exceção para impedir a inicialização da aplicação.

    @classmethod
    def get_all(cls):
        """
        Retorna uma lista de todos os usuários no banco de dados.
        """
        rows = execute_query(
            "SELECT id, name, email, login, password_hash, is_admin, is_active FROM users ORDER BY name", fetchall=True)
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, user_id):
        """
        Retorna um usuário pelo seu ID.
        """
        row = execute_query(
            "SELECT id, name, email, login, password_hash, is_admin, is_active FROM users WHERE id = %s", (user_id,), fetchone=True)
        return cls(*row) if row else None

    @classmethod
    def get_by_login(cls, login):
        """
        Retorna um usuário pelo seu login (nome de usuário).
        """
        row = execute_query(
            "SELECT id, name, email, login, password_hash, is_admin, is_active FROM users WHERE login = %s", (login,), fetchone=True)
        return cls(*row) if row else None

    @classmethod
    def add(cls, name, email, login, password, is_admin=False, is_active=True):
        """
        Adiciona um novo usuário ao banco de dados.
        Retorna uma instância de Usuario em caso de sucesso, None em caso de falha.
        Levanta ValueError em caso de violação de unicidade (login/email duplicado).
        """
        password_hash = generate_password_hash(password)
        try:
            result = execute_query(
                "INSERT INTO users (name, email, login, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (name, email, login, password_hash, is_admin, is_active),
                fetchone=True,
                commit=True
            )
            if result:
                # Retorna a instância do novo usuário com o ID gerado pelo DB.
                return cls(result[0], name, email, login, password_hash, is_admin, is_active)
            return None
        except UniqueViolation as e:
            # Captura a exceção de violação de unicidade e re-lança como ValueError.
            raise ValueError(
                "Erro: Já existe um usuário com este login ou email."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar usuário: {e}")
            raise # Re-lança outras exceções.

    @classmethod
    def update(cls, user_id, name, email, login, new_password=None, is_admin=None, is_active=None):
        """
        Atualiza as informações de um usuário existente.
        Retorna a instância do usuário atualizado, ou None se o usuário não for encontrado.
        Levanta ValueError em caso de violação de unicidade.
        """
        user = cls.get_by_id(user_id)
        if not user:
            return None # Usuário não encontrado para atualização.

        password_hash_to_save = user.password_hash
        if new_password:
            # Se uma nova senha for fornecida, gera um novo hash.
            password_hash_to_save = generate_password_hash(new_password)

        # Mantém o valor existente se o novo valor for None.
        is_admin_to_save = user.is_admin if is_admin is None else is_admin
        is_active_to_save = user.is_active if is_active is None else is_active

        try:
            query = "UPDATE users SET name = %s, email = %s, login = %s, password_hash = %s, is_admin = %s, is_active = %s WHERE id = %s"
            params = (name, email, login, password_hash_to_save,
                      is_admin_to_save, is_active_to_save, user_id)
            if execute_query(query, params, commit=True):
                # Retorna uma nova instância do usuário com os dados atualizados.
                return cls(user_id, name, email, login, password_hash_to_save, is_admin_to_save, is_active_to_save)
            return None
        except UniqueViolation as e:
            # Captura a exceção de violação de unicidade.
            raise ValueError(
                "Erro: Já existe outro usuário com este login ou email."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar usuário: {e}")
            raise # Re-lança outras exceções.

    @classmethod
    def delete(cls, user_id):
        """
        Deleta um usuário do banco de dados pelo seu ID.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM users WHERE id = %s"
        params = (user_id,)
        return execute_query(query, params, commit=True) # Retorna True se a exclusão foi bem-sucedida.

