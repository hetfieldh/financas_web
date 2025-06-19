# models/movimento_renda_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from datetime import datetime
from decimal import Decimal


class MovimentoRenda:  # Classe permanece no singular
    """
    Representa o registro de um movimento específico (pagamento) de um item de renda
    para um determinado mês de referência.
    """

    def __init__(self, id, user_id, renda_id, mes_ref, mes_pagto, valor):
        self.id = id
        self.user_id = user_id
        self.renda_id = renda_id
        self.mes_ref = mes_ref  # datetime.date para AAAA-MM
        self.mes_pagto = mes_pagto  # datetime.date para AAAA-MM
        self.valor = valor  # Decimal para precisão monetária

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_renda' no banco de dados se ela ainda não existir.
        (O nome da tabela no banco de dados continua no plural para consistência com convenções SQL)
        Inclui chaves estrangeiras e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_renda (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            renda_id INTEGER NOT NULL,
            mes_ref DATE NOT NULL,
            mes_pagto DATE NOT NULL,
            valor DECIMAL(10, 2) NOT NULL,
            
            UNIQUE (user_id, renda_id, mes_ref, mes_pagto),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (renda_id) REFERENCES rendas(id) ON DELETE CASCADE
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
        Retorna uma lista de todos os movimentos de renda para um usuário específico.
        Os objetos de Renda associados são buscados em separado nas rotas para evitar junções complexas aqui.
        Ordena por mes_ref decrescente e id.
        """
        rows = execute_query(
            """
            SELECT id, user_id, renda_id, mes_ref, mes_pagto, valor 
            FROM movimentos_renda 
            WHERE user_id = %s 
            ORDER BY mes_ref DESC, mes_pagto DESC, id DESC
            """,
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_renda_id, user_id):
        """
        Retorna um movimento de renda pelo seu ID e ID do usuário.
        """
        row = execute_query(
            """
            SELECT id, user_id, renda_id, mes_ref, mes_pagto, valor 
            FROM movimentos_renda 
            WHERE id = %s AND user_id = %s
            """,
            (movimento_renda_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, renda_id, mes_ref_str, mes_pagto_str, valor):
        """
        Adiciona um novo movimento de renda ao banco de dados.
        mes_ref_str e mes_pagto_str devem estar no formato 'YYYY-MM'.
        """
        try:
            mes_ref = datetime.strptime(mes_ref_str, '%Y-%m').date()
            mes_pagto = datetime.strptime(mes_pagto_str, '%Y-%m').date()

            if not isinstance(valor, Decimal):
                raise TypeError("Valor deve ser do tipo Decimal.")
            if valor == 0:
                raise ValueError("O valor deve ser maior que zero.")

            result = execute_query(
                """
                INSERT INTO movimentos_renda (user_id, renda_id, mes_ref, mes_pagto, valor) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id
                """,
                (user_id, renda_id, mes_ref, mes_pagto, valor),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, renda_id, mes_ref, mes_pagto, valor)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um movimento de renda registrado para este item de renda, mês de referência e mês de pagamento."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Item de renda ou usuário não encontrado."
            ) from e
        except ValueError as e:
            raise ValueError(f"Erro de validação nos dados: {e}") from e
        except Exception as e:
            print(f"Erro ao adicionar movimento de renda: {e}")
            raise

    @classmethod
    def update(cls, movimento_renda_id, user_id, renda_id, mes_ref_str, mes_pagto_str, valor):
        """
        Atualiza as informações de um movimento de renda existente.
        """
        existing_item = cls.get_by_id(movimento_renda_id, user_id)
        if not existing_item:
            return None

        try:
            mes_ref = datetime.strptime(mes_ref_str, '%Y-%m').date()
            mes_pagto = datetime.strptime(mes_pagto_str, '%Y-%m').date()

            if not isinstance(valor, Decimal):
                raise TypeError("Valor deve ser do tipo Decimal.")
            if valor == 0:
                raise ValueError("O valor deve ser maior que zero.")

            # Verificar se a nova combinação user_id, renda_id, mes_ref, mes_pagto
            # já existe para outro ID (evitar UniqueViolation ao atualizar para si mesmo)
            check_query = """
            SELECT id FROM movimentos_renda 
            WHERE user_id = %s AND renda_id = %s AND mes_ref = %s AND mes_pagto = %s AND id != %s
            """
            existing_duplicate = execute_query(
                check_query, (user_id, renda_id, mes_ref, mes_pagto, movimento_renda_id), fetchone=True)
            if existing_duplicate:
                raise ValueError(
                    "Erro: Já existe um movimento de renda com esta combinação de item de renda, mês de referência e mês de pagamento."
                )

            query = """
            UPDATE movimentos_renda 
            SET renda_id = %s, mes_ref = %s, mes_pagto = %s, valor = %s 
            WHERE id = %s AND user_id = %s
            """
            params = (renda_id, mes_ref, mes_pagto,
                      valor, movimento_renda_id, user_id)

            if execute_query(query, params, commit=True):
                return cls(movimento_renda_id, user_id, renda_id, mes_ref, mes_pagto, valor)
            return None
        except UniqueViolation as e:
            # Esta UniqueViolation é mais específica para o update, deve ser tratada pelo check_query acima
            raise ValueError(
                "Erro: Já existe um movimento de renda registrado para esta combinação (item, mês ref, mês pagto)."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Item de renda ou usuário não encontrado."
            ) from e
        except ValueError as e:
            raise ValueError(f"Erro de validação nos dados: {e}") from e
        except Exception as e:
            print(f"Erro ao atualizar movimento de renda: {e}")
            raise

    @classmethod
    def delete(cls, movimento_renda_id, user_id):
        """
        Deleta um movimento de renda do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM movimentos_renda WHERE id = %s AND user_id = %s"
        params = (movimento_renda_id, user_id)
        return execute_query(query, params, commit=True)
