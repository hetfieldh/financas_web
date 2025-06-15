from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class DespesaReceita:
    """
    Representa um item de despesa ou receita de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, despesa_receita, tipo):
        self.id = id
        self.user_id = user_id
        self.despesa_receita = despesa_receita
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'despesas_receitas' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chave estrangeira para 'users' e restri\u00e7\u00e3o de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS despesas_receitas (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            despesa_receita VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Op\u00e7\u00f5es: Receita, Despesa
            
            UNIQUE (user_id, despesa_receita, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'despesas_receitas' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'despesas_receitas': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os itens de despesa/receita de um usu\u00e1rio espec\u00edfico.
        Ordena por despesa_receita e tipo.
        """
        rows = execute_query(
            "SELECT id, user_id, despesa_receita, tipo FROM despesas_receitas WHERE user_id = %s ORDER BY despesa_receita, tipo",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, item_id, user_id):
        """
        Retorna um item de despesa/receita pelo seu ID e ID do usu\u00e1rio.
        """
        row = execute_query(
            "SELECT id, user_id, despesa_receita, tipo FROM despesas_receitas WHERE id = %s AND user_id = %s",
            (item_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, despesa_receita, tipo):
        """
        Adiciona um novo item de despesa/receita ao banco de dados.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou chave estrangeira.
        """
        try:
            result = execute_query(
                "INSERT INTO despesas_receitas (user_id, despesa_receita, tipo) VALUES (%s, %s, %s) RETURNING id",
                (user_id, despesa_receita, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, despesa_receita, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe um item de despesa/receita com esta combina\u00e7\u00e3o de descri\u00e7\u00e3o e tipo para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usu\u00e1rio n\u00e3o encontrado. N\u00e3o \u00e9 poss\u00edvel adicionar despesa/receita."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar despesa/receita: {e}")
            raise

    @classmethod
    def update(cls, item_id, user_id, despesa_receita, tipo):
        """
        Atualiza as informa\u00e7\u00f5es de um item de despesa/receita existente.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou se o item n\u00e3o for encontrado.
        """
        existing_item = cls.get_by_id(item_id, user_id)
        if not existing_item:
            return None  # Item n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        try:
            query = "UPDATE despesas_receitas SET despesa_receita = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (despesa_receita, tipo, item_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(item_id, user_id, despesa_receita, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe outro item de despesa/receita com esta combina\u00e7\u00e3o de descri\u00e7\u00e3o e tipo para este usu\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar despesa/receita: {e}")
            raise

    @classmethod
    def delete(cls, item_id, user_id):
        """
        Deleta um item de despesa/receita do banco de dados.
        Retorna True em caso de sucesso, False caso contr\u00e1rio.
        """
        query = "DELETE FROM despesas_receitas WHERE id = %s AND user_id = %s"
        params = (item_id, user_id)
        return execute_query(query, params, commit=True)
