# models/parcela_crediario_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date


class ParcelaCrediario:
    """
    Representa uma parcela individual de um movimento de crediário.
    """

    def __init__(self, id, movimento_crediario_id, numero_parcela, vencimento_mes, vencimento_ano, valor_parcela):
        self.id = id
        self.movimento_crediario_id = movimento_crediario_id
        self.numero_parcela = numero_parcela
        self.vencimento_mes = vencimento_mes
        self.vencimento_ano = vencimento_ano
        self.valor_parcela = valor_parcela

    @staticmethod
    def create_table():
        """
        Cria a tabela 'parcelas_crediario' no banco de dados se ela ainda não existir.
        Inclui chave estrangeira para 'movimentos_crediario' e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS parcelas_crediario (
            id SERIAL PRIMARY KEY,
            movimento_crediario_id INTEGER NOT NULL,
            numero_parcela INTEGER NOT NULL,
            vencimento_mes INTEGER NOT NULL,
            vencimento_ano INTEGER NOT NULL,
            valor_parcela NUMERIC(15, 2) NOT NULL,
            
            UNIQUE (movimento_crediario_id, numero_parcela),
            
            FOREIGN KEY (movimento_crediario_id) REFERENCES movimentos_crediario(id) ON DELETE CASCADE,
            
            CHECK (numero_parcela >= 1),
            CHECK (vencimento_mes >= 1 AND vencimento_mes <= 12),
            CHECK (vencimento_ano >= 2000 AND vencimento_ano <= 2100)
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'parcelas_crediario' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'parcelas_crediario': {e}")
            raise

    @classmethod
    def get_by_movimento_id(cls, movimento_crediario_id):
        """
        Retorna todas as parcelas associadas a um movimento de crediário específico.
        """
        rows = execute_query(
            "SELECT id, movimento_crediario_id, numero_parcela, vencimento_mes, vencimento_ano, valor_parcela "
            "FROM parcelas_crediario WHERE movimento_crediario_id = %s ORDER BY numero_parcela",
            (movimento_crediario_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def add(cls, movimento_crediario_id, numero_parcela, vencimento_mes, vencimento_ano, valor_parcela):
        """
        Adiciona uma nova parcela ao banco de dados.
        """
        try:
            result = execute_query(
                "INSERT INTO parcelas_crediario (movimento_crediario_id, numero_parcela, vencimento_mes, vencimento_ano, valor_parcela) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (movimento_crediario_id, numero_parcela,
                 vencimento_mes, vencimento_ano, valor_parcela),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], movimento_crediario_id, numero_parcela, vencimento_mes, vencimento_ano, valor_parcela)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe uma parcela com este número para este movimento de crediário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Movimento de Crediário não encontrado. Não é possível adicionar parcela."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar parcela de crediário: {e}")
            raise

    @staticmethod
    def delete_by_movimento_id(movimento_crediario_id):
        """
        Deleta todas as parcelas associadas a um movimento de crediário específico.
        Retorna True se a operação foi bem sucedida, False caso contrário.
        """
        query = """
            DELETE FROM parcelas_crediario WHERE movimento_crediario_id = %s;
        """
        try:
            return execute_query(query, (movimento_crediario_id,), commit=True)
        except Exception as e:
            print(f"Erro ao deletar parcelas de crediário por movimento: {e}")
            return False

    @classmethod
    def delete(cls, parcela_id):
        """
        Deleta uma parcela do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM parcelas_crediario WHERE id = %s"
        params = (parcela_id,)
        try:
            return execute_query(query, params, commit=True)
        except ForeignKeyViolation as e:
            raise ValueError(
                "Não é possível deletar esta parcela de crediário, pois ela possui lançamento ou vínculo com outra tabela. Remova as associações primeiro."
            ) from e
        except Exception as e:
            print(f"Erro inesperado ao deletar parcela de crediário: {e}")
            raise
