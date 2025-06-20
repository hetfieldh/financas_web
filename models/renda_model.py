# models/renda_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class Renda:
    """
    Representa um tipo de renda para um usuário no sistema.
    """

    def __init__(self, id, user_id, descricao, tipo):
        self.id = id
        self.user_id = user_id
        self.descricao = descricao
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'renda' no banco de dados se ela ainda não existir.
        Inclui chave estrangeira para 'usuario' e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS renda (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,

            UNIQUE (user_id, descricao, tipo),

            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'renda' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'renda': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todas as rendas de um usuário específico.
        """
        rows = execute_query(
            "SELECT id, user_id, descricao, tipo FROM renda WHERE user_id = %s ORDER BY descricao, tipo",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, renda_id, user_id):
        """
        Retorna uma renda pelo seu ID e ID do usuário.
        """
        row = execute_query(
            "SELECT id, user_id, descricao, tipo FROM renda WHERE id = %s AND user_id = %s",
            (renda_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, descricao, tipo):
        """
        Adiciona um novo tipo de renda ao banco de dados.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
        """
        try:
            result = execute_query(
                "INSERT INTO renda (user_id, descricao, tipo) VALUES (%s, %s, %s) RETURNING id",
                (user_id, descricao, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, descricao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe uma renda com esta descrição e tipo para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar a renda."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar renda: {e}")
            raise

    @classmethod
    def update(cls, renda_id, user_id, descricao, tipo):
        """
        Atualiza as informações de um tipo de renda existente.
        Levanta ValueError em caso de violação de unicidade ou se a renda não for encontrada.
        """
        existing_renda = cls.get_by_id(renda_id, user_id)
        if not existing_renda:
            return None
        try:
            query = "UPDATE renda SET descricao = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (descricao, tipo, renda_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(renda_id, user_id, descricao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outra renda com esta descrição e tipo para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar renda: {e}")
            raise

    @classmethod
    def delete(cls, renda_id, user_id):
        """
        Deleta um tipo de renda do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM renda WHERE id = %s AND user_id = %s"
        params = (renda_id, user_id)
        return execute_query(query, params, commit=True)
