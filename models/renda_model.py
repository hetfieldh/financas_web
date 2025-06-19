# models/renda_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class Renda:
    """
    Representa um item de renda (provento, desconto, benefício ou outros) de um usuário no sistema.
    """

    def __init__(self, id, user_id, descricao, tipo):
        self.id = id
        self.user_id = user_id
        self.descricao = descricao
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'rendas' no banco de dados se ela ainda não existir.
        Inclui chave estrangeira para 'users' e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS rendas (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('Provento', 'Desconto', 'Benefício', 'Outros')),
            
            UNIQUE (user_id, descricao, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'rendas' verificada/criada com sucesso.")
        except Exception as e:
            print(f"ERRO CRÍTICO ao criar/verificar tabela 'rendas': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os itens de renda de um usuário específico.
        Ordena por descricao.
        """
        rows = execute_query(
            "SELECT id, user_id, descricao, tipo FROM rendas WHERE user_id = %s ORDER BY descricao",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, renda_id, user_id):
        """
        Retorna um item de renda pelo seu ID e ID do usuário.
        """
        row = execute_query(
            "SELECT id, user_id, descricao, tipo FROM rendas WHERE id = %s AND user_id = %s",
            (renda_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, descricao, tipo):
        """
        Adiciona um novo item de renda ao banco de dados.
        """
        try:
            result = execute_query(
                "INSERT INTO rendas (user_id, descricao, tipo) VALUES (%s, %s, %s) RETURNING id",
                (user_id, descricao, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, descricao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Você já possui um item de renda com esta descrição e tipo."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Verifique o user_id."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar item de renda: {e}")
            raise

    @classmethod
    def update(cls, renda_id, user_id, descricao, tipo):
        """
        Atualiza as informações de um item de renda existente.
        """
        existing_item = cls.get_by_id(renda_id, user_id)
        if not existing_item:
            return None

        try:
            query = "UPDATE rendas SET descricao = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (descricao, tipo, renda_id, user_id)

            if execute_query(query, params, commit=True):
                return cls(renda_id, user_id, descricao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Você já possui outro item de renda com esta descrição e tipo."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Verifique o user_id."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar item de renda: {e}")
            raise

    @classmethod
    def delete(cls, renda_id, user_id):
        """
        Deleta um item de renda do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM rendas WHERE id = %s AND user_id = %s"
        params = (renda_id, user_id)
        return execute_query(query, params, commit=True)
