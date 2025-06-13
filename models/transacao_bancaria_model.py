from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class TransacaoBancaria:
    """
    Representa uma transa\u00e7\u00e3o banc\u00e1ria de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, transacao, tipo):
        self.id = id
        self.user_id = user_id
        self.transacao = transacao
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'transacoes_bancarias' no banco de dados se ela ainda n\u00e3o existir.
        Inclui uma chave estrangeira para a tabela 'users'.
        """
        query = """
        CREATE TABLE IF NOT EXISTS transacoes_bancarias (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transacao VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Op\u00e7\u00f5es: Cr\u00e9dito, D\u00e9bito
            UNIQUE (user_id, transacao, tipo),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'transacoes_bancarias' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'transacoes_bancarias': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todas as transa\u00e7\u00f5es banc\u00e1rias de um usu\u00e1rio espec\u00edfico.
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
        Retorna uma transa\u00e7\u00e3o banc\u00e1ria pelo seu ID e ID do usu\u00e1rio, garantindo que o usu\u00e1rio \u00e9 o propriet\u00e1rio.
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
        Adiciona uma nova transa\u00e7\u00e3o banc\u00e1ria ao banco de dados.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou chave estrangeira.
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
                "Erro: J\u00e1 existe uma transa\u00e7\u00e3o banc\u00e1ria com esta combina\u00e7\u00e3o de transa\u00e7\u00e3o e tipo para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usu\u00e1rio n\u00e3o encontrado. N\u00e3o \u00e9 poss\u00edvel adicionar transa\u00e7\u00e3o banc\u00e1ria."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar transa\u00e7\u00e3o banc\u00e1ria: {e}")
            raise

    @classmethod
    def update(cls, transacao_id, user_id, transacao, tipo):
        """
        Atualiza as informa\u00e7\u00f5es de uma transa\u00e7\u00e3o banc\u00e1ria existente.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou se a transa\u00e7\u00e3o n\u00e3o for encontrada.
        """
        # Primeiro, verifica se a transa\u00e7\u00e3o existe e pertence ao usu\u00e1rio
        existing_transacao = cls.get_by_id(transacao_id, user_id)
        if not existing_transacao:
            return None  # Transa\u00e7\u00e3o n\u00e3o encontrada ou n\u00e3o pertence ao usu\u00e1rio

        try:
            query = "UPDATE transacoes_bancarias SET transacao = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (transacao, tipo, transacao_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(transacao_id, user_id, transacao, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe outra transa\u00e7\u00e3o banc\u00e1ria com esta combina\u00e7\u00e3o de transa\u00e7\u00e3o e tipo para este usu\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar transa\u00e7\u00e3o banc\u00e1ria: {e}")
            raise

    @classmethod
    def delete(cls, transacao_id, user_id):
        """
        Deleta uma transa\u00e7\u00e3o banc\u00e1ria do banco de dados pelo seu ID e ID do usu\u00e1rio.
        Retorna True em caso de sucesso, False caso contr\u00e1rio.
        """
        # Garante que apenas o propriet\u00e1rio pode deletar
        query = "DELETE FROM transacoes_bancarias WHERE id = %s AND user_id = %s"
        params = (transacao_id, user_id)
        return execute_query(query, params, commit=True)
