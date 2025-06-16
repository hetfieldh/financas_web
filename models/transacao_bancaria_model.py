# models/transacao_bancaria_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class TransacaoBancaria:
    """
    Representa uma transação bancária de um usuário no sistema.
    """

    def __init__(self, id, user_id, transacao, tipo):
        self.id = id
        self.user_id = user_id
        self.transacao = transacao
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'transacoes_bancarias' no banco de dados se ela ainda não existir.
        Inclui uma chave estrangeira para a tabela 'users'.
        """
        query = """
        CREATE TABLE IF NOT EXISTS transacoes_bancarias (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transacao VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Opções: Crédito, Débito
            UNIQUE (user_id, transacao, tipo),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'transacoes_bancarias' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'transacoes_bancarias': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todas as transações bancárias de um usuário específico.
        """
        rows = execute_query(
            "SELECT id, user_id, transacao, tipo FROM transacoes_bancarias WHERE user_id = %s ORDER BY transacao",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, transacao_id, user_id):
        """
        Retorna uma transação bancária pelo seu ID e ID do usuário, garantindo que o usuário é o proprietário.
        """
        row = execute_query(
            "SELECT id, user_id, transacao, tipo FROM transacoes_bancarias WHERE id = %s AND user_id = %s",
            (transacao_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, transacao, tipo):
        """
        Adiciona uma nova transação bancária ao banco de dados.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
        """
        try:
            result = execute_query(
                "INSERT INTO transacoes_bancarias (user_id, transacao, tipo) VALUES (%s, %s, %s) RETURNING id",
                (user_id, transacao, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, transacao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe uma transação bancária com esta combinação de transação e tipo para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar transação bancária."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar transação bancária: {e}")
            raise

    @classmethod
    def update(cls, transacao_id, user_id, transacao, tipo):
        """
        Atualiza as informações de uma transação bancária existente.
        Levanta ValueError em caso de violação de unicidade ou se a transação não for encontrada.
        """
        existing_transacao = cls.get_by_id(transacao_id, user_id)
        if not existing_transacao:
            return None

        try:
            query = "UPDATE transacoes_bancarias SET transacao = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (transacao, tipo, transacao_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(transacao_id, user_id, transacao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outra transação bancária com esta combinação de transação e tipo para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar transação bancária: {e}")
            raise

    @classmethod
    def delete(cls, transacao_id, user_id):
        """
        Deleta uma transação bancária do banco de dados pelo seu ID e ID do usuário.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM transacoes_bancarias WHERE id = %s AND user_id = %s"
        params = (transacao_id, user_id)
        return execute_query(query, params, commit=True)
