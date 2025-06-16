# models/movimento_bancario_model.py
from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date, datetime, timedelta


class MovimentoBancario:
    """
    Representa um movimento bancário (receita ou despesa) de um usuário no sistema.
    """

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
        """
        Cria a tabela 'movimentos_bancarios' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users', 'contas_bancarias' e 'transacoes_bancarias',
        e restrições de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            conta_bancaria_id INTEGER NOT NULL,
            transacao_bancaria_id INTEGER NOT NULL, -- Corrigido aqui
            data DATE NOT NULL,
            valor NUMERIC(15, 2) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- "Receita" ou "Despesa"
            
            -- Restrição de unicidade para evitar movimentos idênticos duplicados
            UNIQUE (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo), -- Corrigido aqui
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias(id) ON DELETE CASCADE,
            FOREIGN KEY (transacao_bancaria_id) REFERENCES transacoes_bancarias(id) ON DELETE CASCADE -- Corrigido aqui
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
        """
        Retorna uma lista de todos os movimentos bancários de um usuário específico.
        Ordena por data descendente.
        """
        rows = execute_query(
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE user_id = %s ORDER BY data DESC",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento bancário pelo seu ID e ID do usuário.
        """
        row = execute_query(
            # Corrigido aqui
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE id = %s AND user_id = %s",
            (movimento_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        """
        Adiciona um novo movimento bancário ao banco de dados e atualiza o saldo da conta.
        """
        try:
            result = execute_query(
                "INSERT INTO movimentos_bancarios (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, conta_bancaria_id, transacao_bancaria_id,
                 data, valor, tipo),
                fetchone=True,
                commit=False
            )
            movimento_id = result[0] if result else None

            if movimento_id:
                # Atualiza o saldo_atual da conta bancária
                # O cálculo do saldo agora é feito diretamente na query de update para atomicidade.
                if tipo == 'Receita':
                    update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
                else:
                    update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"

                update_success = execute_query(
                    update_query,
                    (valor, conta_bancaria_id, user_id),
                    commit=True
                )

                if update_success:
                    return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
                else:
                    raise Exception(
                        "Falha ao atualizar o saldo da conta bancária.")
            return None

        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um movimento bancário com esta combinação de dados para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Conta Bancária, Transação ou Usuário não encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento bancário: {e}")
            raise

    @classmethod
    def update(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo, old_valor, old_tipo):
        """
        Atualiza um movimento bancário existente e ajusta o saldo da conta.
        Necessita dos valores antigos para calcular o ajuste no saldo.
        """
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None

        try:
            execute_query("BEGIN", commit=False)
            if old_tipo == 'Receita':
                revert_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"
            else:
                revert_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
            execute_query(revert_query, (old_valor,
                          existing_movimento.conta_bancaria_id, user_id), commit=False)

            query = "UPDATE movimentos_bancarios SET conta_bancaria_id = %s, transacao_bancaria_id = %s, data = %s, valor = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (conta_bancaria_id, transacao_bancaria_id, data,
                      valor, tipo, movimento_id, user_id)  # Corrigido aqui
            update_mov_success = execute_query(query, params, commit=False)

            if not update_mov_success:
                execute_query("ROLLBACK", commit=True)
                raise Exception(
                    "Falha ao atualizar o registro do movimento bancário.")

            if tipo == 'Receita':
                apply_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
            else:
                apply_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"
            apply_success = execute_query(
                apply_query, (valor, conta_bancaria_id, user_id), commit=True)

            if apply_success:
                return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
            else:
                execute_query("ROLLBACK", commit=True)
                raise Exception(
                    "Falha ao aplicar o novo saldo na conta bancária.")

        except UniqueViolation as e:
            execute_query("ROLLBACK", commit=True)
            raise ValueError(
                "Erro: Já existe outro movimento bancário com esta combinação de dados para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            execute_query("ROLLBACK", commit=True)
            raise ValueError(
                "Erro: Conta Bancária, Transação ou Usuário não encontrado."
            ) from e
        except Exception as e:
            execute_query("ROLLBACK", commit=True)
            print(f"Erro ao atualizar movimento bancário: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, valor, tipo):
        """
        Deleta um movimento bancário do banco de dados e ajusta o saldo da conta.
        """
        try:
            execute_query("BEGIN", commit=False)
            if tipo == 'Receita':
                update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"
            else:  # tipo == 'Despesa'
                update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"

            update_success = execute_query(
                update_query,
                (valor, conta_bancaria_id, user_id),
                commit=False
            )

            if not update_success:
                execute_query("ROLLBACK", commit=True)
                raise Exception(
                    "Falha ao ajustar o saldo da conta bancária antes de deletar o movimento.")

            query = "DELETE FROM movimentos_bancarios WHERE id = %s AND user_id = %s AND conta_bancaria_id = %s AND transacao_bancaria_id = %s"
            params = (movimento_id, user_id, conta_bancaria_id,
                      transacao_bancaria_id)
            delete_success = execute_query(query, params, commit=True)

            if delete_success:
                return True
            else:
                execute_query("ROLLBACK", commit=True)
                return False

        except Exception as e:
            execute_query("ROLLBACK", commit=True)
            print(f"Erro ao deletar movimento bancário: {e}")
            raise

    @classmethod
    def get_by_account_and_month(cls, user_id, conta_bancaria_id, year, month):
        """
        Retorna uma lista de movimentos bancários para uma conta específica
        dentro de um determinado mês e ano.
        Ordena por data e depois por id.
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        rows = execute_query(
            # Corrigido aqui
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE user_id = %s AND conta_bancaria_id = %s "
            "AND data >= %s AND data <= %s ORDER BY data, id",
            (user_id, conta_bancaria_id, start_date, end_date),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_balance_up_to_date(cls, user_id, conta_bancaria_id, end_date_exclusive):
        """
        Calcula o saldo de uma conta bancária até uma data específica (exclusiva).
        Considera o saldo inicial da conta + todos os movimentos até a data informada.
        """
        from models.conta_bancaria_model import ContaBancaria

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
