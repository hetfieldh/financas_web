# models/despesa_fixa_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date, datetime


class DespesaFixa:
    """
    Representa um item de despesa fixa de um usuário no sistema.
    """

    def __init__(self, id, user_id, despesa_receita_id, mes_ano, valor):
        self.id = id
        self.user_id = user_id
        self.despesa_receita_id = despesa_receita_id
        self.mes_ano = mes_ano
        self.valor = valor

    @staticmethod
    def create_table():
        """
        Cria a tabela 'despesas_fixas' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users' e 'despesas_receitas' e restrições de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS despesas_fixas (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            despesa_receita_id INTEGER NOT NULL,
            mes_ano DATE NOT NULL, 
            valor NUMERIC(15, 2) NOT NULL,
            
            UNIQUE (user_id, despesa_receita_id, mes_ano),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (despesa_receita_id) REFERENCES despesas_receitas(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'despesas_fixas' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'despesas_fixas': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todas as despesas fixas de um usuário específico.
        Ordena por mes_ano descendente e valor.
        """
        rows = execute_query(
            "SELECT id, user_id, despesa_receita_id, mes_ano, valor FROM despesas_fixas WHERE user_id = %s ORDER BY mes_ano DESC, valor",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, despesa_fixa_id, user_id):
        """
        Retorna um item de despesa fixa pelo seu ID e ID do usuário.
        """
        row = execute_query(
            "SELECT id, user_id, despesa_receita_id, mes_ano, valor FROM despesas_fixas WHERE id = %s AND user_id = %s",
            (despesa_fixa_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, despesa_receita_id, mes_ano_str, valor):
        """
        Adiciona um novo item de despesa fixa ao banco de dados.
        mes_ano_str deve estar no formato 'YYYY-MM'.
        """
        try:
            mes_ano = datetime.strptime(mes_ano_str + '-01', '%Y-%m-%d').date()

            result = execute_query(
                "INSERT INTO despesas_fixas (user_id, despesa_receita_id, mes_ano, valor) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, despesa_receita_id, mes_ano, valor),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, despesa_receita_id, mes_ano, valor)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe uma despesa fixa com esta descrição para este mês/ano e usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Item de Despesa/Receita ou Usuário não encontrado."
            ) from e
        except ValueError as e:
            raise ValueError(
                f"Formato de mês/ano inválido. Use 'AAAA-MM'. Detalhes: {e}") from e
        except Exception as e:
            print(f"Erro ao adicionar despesa fixa: {e}")
            raise

    @classmethod
    def update(cls, despesa_fixa_id, user_id, despesa_receita_id, mes_ano_str, valor):
        """
        Atualiza as informações de um item de despesa fixa existente.
        mes_ano_str deve estar no formato 'YYYY-MM'.
        """
        existing_item = cls.get_by_id(despesa_fixa_id, user_id)
        if not existing_item:
            return None

        try:
            mes_ano = datetime.strptime(mes_ano_str + '-01', '%Y-%m-%d').date()

            query = "UPDATE despesas_fixas SET despesa_receita_id = %s, mes_ano = %s, valor = %s WHERE id = %s AND user_id = %s"
            params = (despesa_receita_id, mes_ano,
                      valor, despesa_fixa_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(despesa_fixa_id, user_id, despesa_receita_id, mes_ano, valor)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outra despesa fixa com esta descrição para este mês/ano e usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Item de Despesa/Receita ou Usuário não encontrado."
            ) from e
        except ValueError as e:
            raise ValueError(
                f"Formato de mês/ano inválido. Use 'AAAA-MM'. Detalhes: {e}") from e
        except Exception as e:
            print(f"Erro ao atualizar despesa fixa: {e}")
            raise

    @classmethod
    def delete(cls, despesa_fixa_id, user_id):
        """
        Deleta um item de despesa fixa do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM despesas_fixas WHERE id = %s AND user_id = %s"
        params = (despesa_fixa_id, user_id)
        return execute_query(query, params, commit=True)
