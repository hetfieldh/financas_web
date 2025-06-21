# models/movimento_renda_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date


class MovimentoRenda:
    """
    Representa um registro de um movimento de renda específico de um usuário.
    """

    def __init__(self, id, user_id, renda_id, mes_ref, mes_pagto, valor):
        self.id = id
        self.user_id = user_id
        self.renda_id = renda_id
        self.mes_ref = mes_ref
        self.mes_pagto = mes_pagto
        self.valor = Decimal(valor) if not isinstance(
            valor, Decimal) else valor  

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_renda' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users' e 'renda',
        e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_renda (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            renda_id INTEGER NOT NULL,
            mes_ref DATE NOT NULL,
            mes_pagto DATE NOT NULL,
            valor NUMERIC(15, 2) NOT NULL,
            
            UNIQUE (user_id, renda_id, mes_ref, mes_pagto),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (renda_id) REFERENCES renda(id) ON DELETE RESTRICT
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'movimentos_renda' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'movimentos_renda': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os movimentos de renda de um usuário específico,
        incluindo a descrição e o tipo da renda.
        Ordena por mes_pagto e mes_ref descendente.
        """
        query = """
        SELECT 
            mr.id, mr.user_id, mr.renda_id, mr.mes_ref, mr.mes_pagto, mr.valor, 
            r.descricao AS nome_renda, r.tipo AS tipo_renda
        FROM movimentos_renda mr
        JOIN renda r ON mr.renda_id = r.id
        WHERE mr.user_id = %s 
        ORDER BY mr.mes_pagto DESC, mr.mes_ref DESC;
        """
        rows = execute_query(query, (user_id,), fetchall=True)

        movimentos = []
        if rows:
            for row in rows:
                movimento = cls(row[0], row[1], row[2], row[3], row[4], row[5])
                movimento.nome_renda = row[6]
                movimento.tipo_renda = row[7] 
                movimentos.append(movimento)
        return movimentos

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento de renda pelo seu ID e ID do usuário.
        """
        query = """
        SELECT id, user_id, renda_id, mes_ref, mes_pagto, valor 
        FROM movimentos_renda 
        WHERE id = %s AND user_id = %s;
        """
        row = execute_query(query, (movimento_id, user_id), fetchone=True)
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, renda_id, mes_ref, mes_pagto, valor):
        """
        Adiciona um novo movimento de renda ao banco de dados.
        """
        try:
            valor_decimal = Decimal(valor).quantize(Decimal('0.01'))

            result = execute_query(
                "INSERT INTO movimentos_renda (user_id, renda_id, mes_ref, mes_pagto, valor) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, renda_id, mes_ref, mes_pagto, valor_decimal),
                fetchone=True,
                commit=True
            )
            if result:
                movimento_id_inserido = result[0]
                return cls(movimento_id_inserido, user_id, renda_id, mes_ref, mes_pagto, valor_decimal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um movimento de renda para esta renda, mês de referência e mês de pagamento."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Renda ou Usuário não encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento de renda: {e}")
            raise

    @classmethod
    def update(cls, movimento_id, user_id, renda_id, mes_ref, mes_pagto, valor):
        """
        Atualiza um movimento de renda existente no banco de dados.
        """
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None

        try:
            valor_decimal = Decimal(valor).quantize(Decimal('0.01'))

            query = """
            UPDATE movimentos_renda 
            SET renda_id = %s, mes_ref = %s, mes_pagto = %s, valor = %s 
            WHERE id = %s AND user_id = %s
            """
            params = (renda_id, mes_ref, mes_pagto,
                      valor_decimal, movimento_id, user_id)

            if execute_query(query, params, commit=True):
                return cls(movimento_id, user_id, renda_id, mes_ref, mes_pagto, valor_decimal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro movimento de renda com esta combinação de dados (renda, mês de referência, mês de pagamento) para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Renda ou Usuário não encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar movimento de renda: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id):
        """
        Deleta um movimento de renda do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM movimentos_renda WHERE id = %s AND user_id = %s"
        params = (movimento_id, user_id)
        return execute_query(query, params, commit=True)

    @classmethod
    def get_movimentos_by_mes_pagto(cls, user_id, year, month):
        """
        Retorna todos os movimentos de renda para um determinado mês e ano de pagamento.
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date_exclusive = date(year + 1, 1, 1)
        else:
            end_date_exclusive = date(year, month + 1, 1)

        query = """
        SELECT 
            mr.id, mr.user_id, mr.renda_id, mr.mes_ref, mr.mes_pagto, mr.valor,
            r.descricao AS nome_renda, r.tipo AS tipo_renda
        FROM movimentos_renda mr
        JOIN renda r ON mr.renda_id = r.id
        WHERE mr.user_id = %s 
          AND mr.mes_pagto >= %s 
          AND mr.mes_pagto < %s
        ORDER BY mr.mes_pagto, mr.mes_ref DESC;
        """
        rows = execute_query(
            query,
            (user_id, start_date, end_date_exclusive),
            fetchall=True
        )
        movimentos = []
        if rows:
            for row in rows:
                movimento = cls(row[0], row[1], row[2], row[3], row[4], row[5])
                movimento.nome_renda = row[6]
                movimento.tipo_renda = row[7]
                movimentos.append(movimento)
        return movimentos

    @classmethod
    def get_movimentos_by_mes_ref(cls, user_id, year, month):
        """
        Retorna todos os movimentos de renda para um determinado mês e ano de referência.
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date_exclusive = date(year + 1, 1, 1)
        else:
            end_date_exclusive = date(year, month + 1, 1)

        query = """
        SELECT 
            mr.id, mr.user_id, mr.renda_id, mr.mes_ref, mr.mes_pagto, mr.valor,
            r.descricao AS nome_renda, r.tipo AS tipo_renda
        FROM movimentos_renda mr
        JOIN renda r ON mr.renda_id = r.id
        WHERE mr.user_id = %s 
          AND mr.mes_ref >= %s 
          AND mr.mes_ref < %s
        ORDER BY mr.mes_ref, mr.mes_pagto DESC;
        """
        rows = execute_query(
            query,
            (user_id, start_date, end_date_exclusive),
            fetchall=True
        )
        movimentos = []
        if rows:
            for row in rows:
                movimento = cls(row[0], row[1], row[2], row[3], row[4], row[5])
                movimento.nome_renda = row[6]
                movimento.tipo_renda = row[7]
                movimentos.append(movimento)
        return movimentos
