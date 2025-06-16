# models/crediario_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal


class Crediario:
    """
    Representa um item de crediário de um usuário no sistema.
    """

    def __init__(self, id, user_id, crediario, tipo, final, limite):
        self.id = id
        self.user_id = user_id
        self.crediario = crediario
        self.tipo = tipo
        self.final = final
        self.limite = limite

    @staticmethod
    def create_table():
        """
        Cria a tabela 'crediarios' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users' e restrições de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS crediarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            crediario VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            final INTEGER NOT NULL,
            limite NUMERIC(15, 2) NOT NULL,
            
            UNIQUE (user_id, crediario, tipo, final),
            UNIQUE (user_id, crediario, final),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'crediarios' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'crediarios': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os itens de crediário de um usuário específico.
        """
        rows = execute_query(
            "SELECT id, user_id, crediario, tipo, final, limite FROM crediarios WHERE user_id = %s ORDER BY crediario, final",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, crediario_id, user_id):
        """
        Retorna um item de crediário pelo seu ID e ID do usuário.
        """
        row = execute_query(
            "SELECT id, user_id, crediario, tipo, final, limite FROM crediarios WHERE id = %s AND user_id = %s",
            (crediario_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, crediario, tipo, final, limite):
        """
        Adiciona um novo item de crediário ao banco de dados.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
        """
        try:
            if not (0 <= final <= 9999):
                raise ValueError(
                    "O campo 'Final' deve ser um número inteiro entre 0 e 9999.")

            result = execute_query(
                "INSERT INTO crediarios (user_id, crediario, tipo, final, limite) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, crediario, tipo, final, limite),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, crediario, tipo, final, limite)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um item de crediário com esta combinação para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar crediário."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar crediário: {e}")
            raise

    @classmethod
    def update(cls, crediario_id, user_id, crediario, tipo, final, limite):
        """
        Atualiza as informações de um item de crediário existente.
        Levanta ValueError em caso de violação de unicidade ou se o crediário não for encontrado.
        """
        existing_crediario = cls.get_by_id(crediario_id, user_id)
        if not existing_crediario:
            return None

        try:
            if not (0 <= final <= 9999):
                raise ValueError(
                    "O campo 'Final' deve ser um número inteiro entre 0 e 9999.")

            query = "UPDATE crediarios SET crediario = %s, tipo = %s, final = %s, limite = %s WHERE id = %s AND user_id = %s"
            params = (crediario, tipo, final, limite, crediario_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(crediario_id, user_id, crediario, tipo, final, limite)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro item de crediário com esta combinação para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar crediário: {e}")
            raise

    @classmethod
    def delete(cls, crediario_id, user_id):
        """
        Deleta um item de crediário do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM crediarios WHERE id = %s AND user_id = %s"
        params = (crediario_id, user_id)
        return execute_query(query, params, commit=True)
