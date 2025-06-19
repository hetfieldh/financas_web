# models/movimento_bancario_model.py

from database.db_manager import open_connection
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date, datetime, timedelta
from models.conta_bancaria_model import ContaBancaria
from database.db_manager import execute_query


class MovimentoBancario:
    def __init__(self, id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        self.id = id
        self.user_id = user_id
        self.conta_bancaria_id = conta_bancaria_id
        self.transacao_bancaria_id = transacao_bancaria_id
        self.data = data
        self.valor = valor
        self.tipo = tipo

    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            conta_bancaria_id INTEGER NOT NULL,
            transacao_bancaria_id INTEGER NOT NULL,
            data DATE NOT NULL,
            valor NUMERIC(15, 2) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            
            UNIQUE (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias(id) ON DELETE CASCADE,
            FOREIGN KEY (transacao_bancaria_id) REFERENCES transacoes_bancarias(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'movimentos_bancarios' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'movimentos_bancarios': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        rows = execute_query(
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE user_id = %s ORDER BY data DESC, conta_bancaria_id",
            (user_id,),
            fetchall=True
        )
        if rows:
            return [cls(row[0], row[1], row[2], row[3], row[4], Decimal(str(row[5])), row[6]) for row in rows]
        return []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        row = execute_query(
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE id = %s AND user_id = %s",
            (movimento_id, user_id),
            fetchone=True
        )
        if row:
            row_list = list(row)
            row_list[5] = Decimal(str(row_list[5]))
            return cls(*row_list)
        return None

    @classmethod
    def add(cls, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        conn = None
        try:
            conn = open_connection()
            cursor = conn.cursor()

            conta = ContaBancaria.get_by_id(conta_bancaria_id, user_id)
            if not conta:
                raise ValueError("Conta bancária não encontrada.")

            if tipo == 'Receita':
                ajuste_saldo = valor.copy_abs()
            else:
                ajuste_saldo = -valor.copy_abs()

            saldo_projetado = conta.saldo_atual + ajuste_saldo

            if saldo_projetado < Decimal('0.00'):
                if saldo_projetado < -conta.limite:
                    conn.rollback()
                    raise ValueError(
                        f"Transação excede o limite de cheque especial. "
                        f"Saldo atual: {conta.saldo_atual:.2f}, Limite: {conta.limite:.2f}, Saldo projetado: {saldo_projetado:.2f}"
                    )

            insert_query = """
                INSERT INTO movimentos_bancarios (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
            """
            cursor.execute(insert_query, (user_id, conta_bancaria_id,
                           transacao_bancaria_id, data, valor, tipo))
            movimento_id = cursor.fetchone()[0]

            ContaBancaria.update_saldo(
                conta_bancaria_id, user_id, ajuste_saldo, connection=conn, cursor=cursor)

            conn.commit()

            return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)

        except UniqueViolation as e:
            if conn:
                conn.rollback()
            raise ValueError(
                "Erro: Já existe um movimento bancário com esta combinação de dados para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            if conn:
                conn.rollback()
            raise ValueError(
                "Erro: Conta Bancária, Transação ou Usuário não encontrado."
            ) from e
        except ValueError as e:
            if conn:
                conn.rollback()
            raise e
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao adicionar movimento bancário: {e}")
            raise

        finally:
            if conn:
                conn.close()

    @classmethod
    def update(cls, movimento_id, user_id, nova_conta_bancaria_id, nova_transacao_bancaria_id, nova_data, novo_valor, novo_tipo):
        conn = None
        try:
            conn = open_connection()
            cursor = conn.cursor()

            current_movimento = cls.get_by_id(movimento_id, user_id)
            if not current_movimento:
                raise ValueError(
                    "Movimento bancário não encontrado para atualização ou não autorizado.")

            conta_antiga = ContaBancaria.get_by_id(
                current_movimento.conta_bancaria_id, user_id)
            if not conta_antiga:
                raise ValueError("Conta bancária original não encontrada.")

            conta_nova = conta_antiga
            if current_movimento.conta_bancaria_id != nova_conta_bancaria_id:
                conta_nova = ContaBancaria.get_by_id(
                    nova_conta_bancaria_id, user_id)
                if not conta_nova:
                    raise ValueError("Nova conta bancária não encontrada.")

            if current_movimento.tipo == 'Receita':
                ajuste_reverso_antigo = -current_movimento.valor.copy_abs()
            else:
                ajuste_reverso_antigo = current_movimento.valor.copy_abs()

            if novo_tipo == 'Receita':
                ajuste_novo_saldo = novo_valor.copy_abs()
            else:
                ajuste_novo_saldo = -novo_valor.copy_abs()

            saldo_conta_antiga_apos_reversao = conta_antiga.saldo_atual + ajuste_reverso_antigo

            if current_movimento.conta_bancaria_id != nova_conta_bancaria_id:
                saldo_projetado_conta_nova = conta_nova.saldo_atual + ajuste_novo_saldo
            else:
                saldo_projetado_conta_nova = saldo_conta_antiga_apos_reversao + ajuste_novo_saldo

            if saldo_projetado_conta_nova < Decimal('0.00'):
                if saldo_projetado_conta_nova < -conta_nova.limite:
                    conn.rollback()
                    raise ValueError(
                        f"Atualização excede o limite de cheque especial na conta '{conta_nova.nome_conta}'. "
                        f"Saldo projetado: {saldo_projetado_conta_nova:.2f}, Limite: {conta_nova.limite:.2f}"
                    )

            ContaBancaria.update_saldo(current_movimento.conta_bancaria_id,
                                       user_id, ajuste_reverso_antigo, connection=conn, cursor=cursor)

            update_mov_query = """
                UPDATE movimentos_bancarios
                SET conta_bancaria_id = %s, transacao_bancaria_id = %s, data = %s, valor = %s, tipo = %s
                WHERE id = %s AND user_id = %s;
            """
            cursor.execute(update_mov_query, (nova_conta_bancaria_id, nova_transacao_bancaria_id,
                                              nova_data, novo_valor, novo_tipo, movimento_id, user_id))

            if cursor.rowcount == 0:
                raise ValueError(
                    "Falha ao atualizar o registro do movimento bancário.")

            ContaBancaria.update_saldo(
                nova_conta_bancaria_id, user_id, ajuste_novo_saldo, connection=conn, cursor=cursor)

            conn.commit()

            return cls(movimento_id, user_id, nova_conta_bancaria_id, nova_transacao_bancaria_id, nova_data, novo_valor, novo_tipo)

        except (UniqueViolation, ForeignKeyViolation) as e:
            if conn:
                conn.rollback()
            if isinstance(e, UniqueViolation):
                raise ValueError(
                    "Erro: Já existe outro movimento bancário com esta combinação de dados para este usuário.") from e
            else:
                raise ValueError(
                    "Erro: Nova Conta Bancária, Transação ou Usuário não encontrado.") from e
        except ValueError as e:
            if conn:
                conn.rollback()
            raise e
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao atualizar movimento bancário: {e}")
            raise

        finally:
            if conn:
                conn.close()

    @classmethod
    def delete(cls, movimento_id, user_id):
        conn = None
        try:
            conn = open_connection()
            cursor = conn.cursor()

            movimento_a_deletar = cls.get_by_id(movimento_id, user_id)
            if not movimento_a_deletar:
                raise ValueError(
                    "Movimento bancário não encontrado para exclusão ou não autorizado.")

            if movimento_a_deletar.tipo == 'Receita':
                ajuste_reverso = -movimento_a_deletar.valor.copy_abs()
            else:
                ajuste_reverso = movimento_a_deletar.valor.copy_abs()

            ContaBancaria.update_saldo(
                movimento_a_deletar.conta_bancaria_id, user_id, ajuste_reverso, connection=conn, cursor=cursor)

            delete_query = "DELETE FROM movimentos_bancarios WHERE id = %s AND user_id = %s;"
            cursor.execute(delete_query, (movimento_id, user_id))

            if cursor.rowcount == 0:
                raise ValueError(
                    "Falha ao deletar o registro do movimento bancário.")

            conn.commit()
            return True

        except ValueError as e:
            if conn:
                conn.rollback()
            raise e
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao deletar movimento bancário: {e}")
            raise

        finally:
            if conn:
                conn.close()

    @classmethod
    def get_by_account_and_month(cls, user_id, conta_bancaria_id, year, month):
        start_date = date(year, month, 1)
        next_month = month % 12 + 1
        next_year = year + (month // 12)
        end_date_exclusive = date(next_year, next_month, 1)

        rows = execute_query(
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE user_id = %s AND conta_bancaria_id = %s "
            "AND data >= %s AND data < %s ORDER BY data, id",
            (user_id, conta_bancaria_id, start_date, end_date_exclusive),
            fetchall=True
        )
        if rows:
            return [
                cls(row[0], row[1], row[2], row[3],
                    row[4], Decimal(str(row[5])), row[6])
                for row in rows
            ]
        return []

    @classmethod
    def get_balance_up_to_date(cls, user_id, conta_bancaria_id, end_date_exclusive):
        conta = ContaBancaria.get_by_id(conta_bancaria_id, user_id)
        if not conta:
            return Decimal('0.00')

        initial_balance_from_account = conta.saldo_inicial if conta.saldo_inicial is not None else Decimal(
            '0.00')

        query = """
        SELECT SUM(CASE WHEN tipo = 'Receita' THEN valor ELSE -valor END)
        FROM movimentos_bancarios
        WHERE user_id = %s AND conta_bancaria_id = %s AND data < %s;
        """

        result = execute_query(
            query, (user_id, conta_bancaria_id, end_date_exclusive), fetchone=True)

        movements_balance = result[0] if result and result[0] is not None else Decimal(
            '0.00')

        return initial_balance_from_account + movements_balance
