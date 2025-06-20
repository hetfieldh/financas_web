# models/despesa_receita_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class DespesaReceita:
    """
    Representa um item de despesa ou receita de um usuário no sistema.
    """

    def __init__(self, id, user_id, despesa_receita, tipo):
        self.id = id
        self.user_id = user_id
        self.despesa_receita = despesa_receita
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'despesas_receitas' no banco de dados se ela ainda não existir.
        Inclui chave estrangeira para 'users' e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS despesas_receitas (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            despesa_receita VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Opções: Receita, Despesa
            
            UNIQUE (user_id, despesa_receita, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'despesas_receitas' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'despesas_receitas': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os itens de despesa/receita de um usuário específico.
        Ordena por despesa_receita e tipo.
        """
        rows = execute_query(
            "SELECT id, user_id, despesa_receita, tipo FROM despesas_receitas WHERE user_id = %s ORDER BY tipo DESC, despesa_receita",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, item_id, user_id):
        """
        Retorna um item de despesa/receita pelo seu ID e ID do usuário.
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
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
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
                "Erro: Já existe um item de despesa/receita com esta combinação de descrição e tipo para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar despesa/receita."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar despesa/receita: {e}")
            raise

    @classmethod
    def update(cls, item_id, user_id, despesa_receita, tipo):
        """
        Atualiza as informações de um item de despesa/receita existente.
        Levanta ValueError em caso de violação de unicidade ou se o item não for encontrado.
        """
        existing_item = cls.get_by_id(item_id, user_id)
        if not existing_item:
            return None

        try:
            query = "UPDATE despesas_receitas SET despesa_receita = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (despesa_receita, tipo, item_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(item_id, user_id, despesa_receita, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro item de despesa/receita com esta combinação de descrição e tipo para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar despesa/receita: {e}")
            raise

    @classmethod
    def delete(cls, item_id, user_id):
        """
        Deleta um item de despesa/receita do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM despesas_receitas WHERE id = %s AND user_id = %s"
        params = (item_id, user_id)
        try:
            return execute_query(query, params, commit=True)
        except ForeignKeyViolation as e:
            raise ValueError(
                "Não é possível deletar esta despesa/receita, pois ela possui lançamento ou vínculo com outra tabela. Remova as associações primeiro."
            ) from e
        except Exception as e:
            print(f"Erro inesperado ao deletar despesa/receita: {e}")
            raise
