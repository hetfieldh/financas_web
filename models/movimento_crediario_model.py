# models/movimento_crediario_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from models.parcela_crediario_model import ParcelaCrediario
from calendar import monthrange


class MovimentoCrediario:
    """
    Representa um movimento de crediário (parcelado) de um usuário no sistema.
    """

    def __init__(self, id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
                 valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal):
        self.id = id
        self.user_id = user_id
        self.grupo_crediario_id = grupo_crediario_id
        self.crediario_id = crediario_id
        self.data_compra = data_compra
        self.descricao = descricao
        self.valor_total = valor_total
        self.num_parcelas = num_parcelas
        self.primeira_parcela = primeira_parcela
        self.ultima_parcela = ultima_parcela
        self.valor_parcela_mensal = valor_parcela_mensal

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_crediario' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users', 'grupos_crediario' e 'crediarios',
        e restrições de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_crediario (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            grupo_crediario_id INTEGER NOT NULL,
            crediario_id INTEGER NOT NULL,
            data_compra DATE NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            valor_total NUMERIC(15, 2) NOT NULL,
            num_parcelas INTEGER NOT NULL,
            primeira_parcela DATE NOT NULL,
            ultima_parcela DATE NOT NULL, -- Calculada
            valor_parcela_mensal NUMERIC(15, 2) NOT NULL, -- Calculada
            
            UNIQUE (user_id, grupo_crediario_id, crediario_id, data_compra, valor_total, num_parcelas),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (grupo_crediario_id) REFERENCES grupos_crediario(id) ON DELETE RESTRICT,
            FOREIGN KEY (crediario_id) REFERENCES crediarios(id) ON DELETE RESTRICT,
            
            CHECK (num_parcelas >= 1 AND num_parcelas <= 360) -- Limite de 1 a 360 parcelas
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'movimentos_crediario' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'movimentos_crediario': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os movimentos de crediário de um usuário específico.
        Ordena por data_compra descendente.
        """
        rows = execute_query(
            "SELECT id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao, "
            "valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal "
            "FROM movimentos_crediario WHERE user_id = %s ORDER BY data_compra DESC",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento de crediário pelo seu ID e ID do usuário.
        """
        row = execute_query(
            "SELECT id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao, "
            "valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal "
            "FROM movimentos_crediario WHERE id = %s AND user_id = %s",
            (movimento_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def _calculate_derived_fields(cls, valor_total, num_parcelas, primeira_parcela):
        """
        Calcula a última parcela e o valor da parcela mensal.
        """
        if not isinstance(valor_total, Decimal) or not isinstance(num_parcelas, int):
            raise TypeError(
                "valor_total deve ser Decimal e num_parcelas deve ser int.")
        if num_parcelas <= 0:
            raise ValueError(
                "O número de parcelas deve ser maior que zero.")

        valor_parcela_mensal = valor_total / Decimal(num_parcelas)
        valor_parcela_mensal = valor_parcela_mensal.quantize(Decimal('0.01'))

        ultima_parcela = primeira_parcela + \
            relativedelta(months=num_parcelas - 1)

        return ultima_parcela, valor_parcela_mensal

    @classmethod
    def add(cls, user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
            valor_total, num_parcelas, primeira_parcela):
        """
        Adiciona um novo movimento de crediário, calcula os campos derivados
        e gera as parcelas associadas.
        """
        try:
            ultima_parcela, valor_parcela_mensal = cls._calculate_derived_fields(
                valor_total, num_parcelas, primeira_parcela
            )

            result = execute_query(
                "INSERT INTO movimentos_crediario (user_id, grupo_crediario_id, crediario_id, data_compra, descricao, "
                "valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
                 valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal),
                fetchone=True,
                commit=True
            )
            if result:
                movimento_id_inserido = result[0]

                dia_base_parcela = data_compra.day

                for i in range(num_parcelas):
                    mes_parcela = primeira_parcela.month + i
                    ano_parcela = primeira_parcela.year + \
                        (mes_parcela - 1) // 12
                    mes_parcela = (mes_parcela - 1) % 12 + 1

                    max_dia_mes = monthrange(ano_parcela, mes_parcela)[1]
                    dia_ajustado = min(dia_base_parcela, max_dia_mes)

                    ParcelaCrediario.add(
                        movimento_crediario_id=movimento_id_inserido,
                        numero_parcela=i + 1,
                        vencimento_mes=mes_parcela,
                        vencimento_ano=ano_parcela,
                        valor_parcela=valor_parcela_mensal
                    )

                return cls(movimento_id_inserido, user_id, grupo_crediario_id, crediario_id, data_compra,
                           descricao, valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um movimento de crediário com esta combinação de dados para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Grupo de Crediário, Crediário ou Usuário não encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento de crediário: {e}")
            raise

    @classmethod
    def update(cls, movimento_id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
               valor_total, num_parcelas, primeira_parcela):
        """
        Atualiza um movimento de crediário existente, recalcula os campos derivados
        e atualiza as parcelas associadas (deletando e recriando).
        """
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None

        try:
            ultima_parcela, valor_parcela_mensal = cls._calculate_derived_fields(
                valor_total, num_parcelas, primeira_parcela
            )

            query = "UPDATE movimentos_crediario SET grupo_crediario_id = %s, crediario_id = %s, " \
                    "data_compra = %s, descricao = %s, valor_total = %s, num_parcelas = %s, " \
                    "primeira_parcela = %s, ultima_parcela = %s, valor_parcela_mensal = %s " \
                    "WHERE id = %s AND user_id = %s"

            params = (grupo_crediario_id, crediario_id, data_compra, descricao,
                      valor_total, num_parcelas, primeira_parcela, ultima_parcela,
                      valor_parcela_mensal, movimento_id, user_id)

            if execute_query(query, params, commit=True):
                if not ParcelaCrediario.delete_by_movimento_id(movimento_id):
                    raise Exception(
                        "Falha ao deletar parcelas existentes para o movimento de crediário.")

                dia_base_parcela = data_compra.day

                for i in range(num_parcelas):
                    mes_parcela = primeira_parcela.month + i
                    ano_parcela = primeira_parcela.year + \
                        (mes_parcela - 1) // 12
                    mes_parcela = (mes_parcela - 1) % 12 + 1

                    max_dia_mes = monthrange(ano_parcela, mes_parcela)[1]
                    dia_ajustado = min(dia_base_parcela, max_dia_mes)

                    ParcelaCrediario.add(
                        movimento_crediario_id=movimento_id,
                        numero_parcela=i + 1,
                        vencimento_mes=mes_parcela,
                        vencimento_ano=ano_parcela,
                        valor_parcela=valor_parcela_mensal
                    )
                return cls(movimento_id, user_id, grupo_crediario_id, crediario_id, data_compra,
                           descricao, valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro movimento de crediário com esta combinação de dados para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Grupo de Crediário, Crediário ou Usuário não encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar movimento de crediário: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id):
        """
        Deleta um movimento de crediário do banco de dados.
        As parcelas associadas serão deletadas automaticamente pelo ON DELETE RESTRICT
        definido na chave estrangeira em 'parcelas_crediario'.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM movimentos_crediario WHERE id = %s AND user_id = %s"
        params = (movimento_id, user_id)
        return execute_query(query, params, commit=True)

    @classmethod
    def get_by_crediario_and_month(cls, user_id, crediario_id, year, month):
        """
        Retorna os movimentos de crediário de um usuário para um crediário específico
        e dentro de um determinado mês e ano.
        """
        start_of_month = date(year, month, 1)
        if month == 12:
            end_of_month_exclusive = date(year + 1, 1, 1)
        else:
            end_of_month_exclusive = date(year, month + 1, 1)

        query = """
        SELECT id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao, 
               valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal
        FROM movimentos_crediario 
        WHERE user_id = %s 
          AND crediario_id = %s 
          AND (primeira_parcela < %s OR ultima_parcela >= %s) 
        ORDER BY data_compra DESC;
        """
        rows = execute_query(
            query,
            (user_id, crediario_id, end_of_month_exclusive, start_of_month),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []
