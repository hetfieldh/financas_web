from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date, datetime, timedelta


class MovimentoBancario:
    """
    Representa um movimento banc\u00e1rio (receita ou despesa) de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):  # Corrigido aqui
        self.id = id
        self.user_id = user_id
        self.conta_bancaria_id = conta_bancaria_id
        self.transacao_bancaria_id = transacao_bancaria_id  # Corrigido aqui
        self.data = data
        self.valor = valor
        self.tipo = tipo  # "Receita" ou "Despesa"

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_bancarios' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chaves estrangeiras para 'users', 'contas_bancarias' e 'transacoes_bancarias',
        e restri\u00e7\u00f5es de unicidade.
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
            
            -- Restri\u00e7\u00e3o de unicidade para evitar movimentos id\u00eanticos duplicados
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
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'movimentos_bancarios': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os movimentos banc\u00e1rios de um usu\u00e1rio espec\u00edfico.
        Ordena por data descendente.
        """
        rows = execute_query(
            # Corrigido aqui
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo "
            "FROM movimentos_bancarios WHERE user_id = %s ORDER BY data DESC",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento banc\u00e1rio pelo seu ID e ID do usu\u00e1rio.
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
    def add(cls, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):  # Corrigido aqui
        """
        Adiciona um novo movimento banc\u00e1rio ao banco de dados e atualiza o saldo da conta.
        """
        try:
            result = execute_query(
                # Corrigido aqui
                "INSERT INTO movimentos_bancarios (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, conta_bancaria_id, transacao_bancaria_id,
                 data, valor, tipo),  # Corrigido aqui
                fetchone=True,
                commit=False  # N\u00e3o commitar ainda, parte de uma transa\u00e7\u00e3o maior
            )
            movimento_id = result[0] if result else None

            if movimento_id:
                # Atualiza o saldo_atual da conta banc\u00e1ria
                # O c\u00e1lculo do saldo agora \u00e9 feito diretamente na query de update para atomicidade.
                if tipo == 'Receita':
                    update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
                else:  # tipo == 'Despesa'
                    update_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"

                update_success = execute_query(
                    update_query,
                    (valor, conta_bancaria_id, user_id),
                    commit=True  # Commita aqui a opera\u00e7\u00e3o completa
                )

                if update_success:
                    # Corrigido aqui
                    return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
                else:
                    # Se a atualiza\u00e7\u00e3o do saldo falhar, o movimento n\u00e3o \u00e9 commitado
                    raise Exception(
                        "Falha ao atualizar o saldo da conta banc\u00e1ria.")
            return None

        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe um movimento banc\u00e1rio com esta combina\u00e7\u00e3o de dados para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Conta Banc\u00e1ria, Transa\u00e7\u00e3o ou Usu\u00e1rio n\u00e3o encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento banc\u00e1rio: {e}")
            raise  # Re-lan\u00e7a para o chamador

    @classmethod
    def update(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo, old_valor, old_tipo):  # Corrigido aqui
        """
        Atualiza um movimento banc\u00e1rio existente e ajusta o saldo da conta.
        Necessita dos valores antigos para calcular o ajuste no saldo.
        """
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None  # Movimento n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        try:
            # Iniciar uma transa\u00e7\u00e3o manualmente para garantir atomicidade
            execute_query("BEGIN", commit=False)

            # 1. Reverter o impacto do movimento antigo no saldo
            if old_tipo == 'Receita':
                revert_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"
            else:  # old_tipo == 'Despesa'
                revert_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
            execute_query(revert_query, (old_valor,
                          existing_movimento.conta_bancaria_id, user_id), commit=False)

            # 2. Atualizar o registro do movimento
            query = "UPDATE movimentos_bancarios SET conta_bancaria_id = %s, transacao_bancaria_id = %s, data = %s, valor = %s, tipo = %s WHERE id = %s AND user_id = %s"  # Corrigido aqui
            params = (conta_bancaria_id, transacao_bancaria_id, data,
                      valor, tipo, movimento_id, user_id)  # Corrigido aqui
            update_mov_success = execute_query(query, params, commit=False)

            if not update_mov_success:
                execute_query("ROLLBACK", commit=True)
                raise Exception(
                    "Falha ao atualizar o registro do movimento banc\u00e1rio.")

            # 3. Aplicar o impacto do novo movimento no saldo
            if tipo == 'Receita':
                apply_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual + %s WHERE id = %s AND user_id = %s"
            else:  # tipo == 'Despesa'
                apply_query = "UPDATE contas_bancarias SET saldo_atual = saldo_atual - %s WHERE id = %s AND user_id = %s"
            apply_success = execute_query(
                apply_query, (valor, conta_bancaria_id, user_id), commit=True)

            if apply_success:
                # Corrigido aqui
                return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
            else:
                execute_query("ROLLBACK", commit=True)
                raise Exception(
                    "Falha ao aplicar o novo saldo na conta banc\u00e1ria.")

        except UniqueViolation as e:
            execute_query("ROLLBACK", commit=True)
            raise ValueError(
                "Erro: J\u00e1 existe outro movimento banc\u00e1rio com esta combina\u00e7\u00e3o de dados para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            execute_query("ROLLBACK", commit=True)
            raise ValueError(
                "Erro: Conta Banc\u00e1ria, Transa\u00e7\u00e3o ou Usu\u00e1rio n\u00e3o encontrado."
            ) from e
        except Exception as e:
            execute_query("ROLLBACK", commit=True)
            print(f"Erro ao atualizar movimento banc\u00e1rio: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, valor, tipo):  # Corrigido aqui
        """
        Deleta um movimento banc\u00e1rio do banco de dados e ajusta o saldo da conta.
        """
        try:
            # Iniciar uma transa\u00e7\u00e3o manualmente para garantir atomicidade
            execute_query("BEGIN", commit=False)

            # 1. Ajustar o saldo da conta banc\u00e1ria
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
                    "Falha ao ajustar o saldo da conta banc\u00e1ria antes de deletar o movimento.")

            # 2. Deletar o movimento
            query = "DELETE FROM movimentos_bancarios WHERE id = %s AND user_id = %s AND conta_bancaria_id = %s AND transacao_bancaria_id = %s"  # Corrigido aqui
            params = (movimento_id, user_id, conta_bancaria_id,
                      transacao_bancaria_id)  # Corrigido aqui
            delete_success = execute_query(query, params, commit=True)

            if delete_success:
                return True
            else:
                execute_query("ROLLBACK", commit=True)
                return False

        except Exception as e:
            execute_query("ROLLBACK", commit=True)
            print(f"Erro ao deletar movimento banc\u00e1rio: {e}")
            raise  # Re-lan\u00e7a para o chamador

    @classmethod
    def get_by_account_and_month(cls, user_id, conta_bancaria_id, year, month):
        """
        Retorna uma lista de movimentos banc\u00e1rios para uma conta espec\u00edfica
        dentro de um determinado m\u00eas e ano.
        Ordena por data e depois por id.
        """
        # Calcular o in\u00edcio e o fim do m\u00eas
        start_date = date(year, month, 1)
        # Pr\u00f3ximo m\u00eas, subtrai um dia para pegar o \u00faltimo dia do m\u00eas atual
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
        Calcula o saldo de uma conta banc\u00e1ria at\u00e9 uma data espec\u00edfica (exclusiva).
        Considera o saldo inicial da conta + todos os movimentos at\u00e9 a data informada.
        """
        from models.conta_bancaria_model import ContaBancaria  # Importa aqui para evitar importa\u00e7\u00e3o circular

        conta = ContaBancaria.get_by_id(conta_bancaria_id, user_id)
        if not conta:
            # Ou levantar um erro, dependendo do tratamento desejado
            return Decimal('0.00')

        initial_balance_from_account = conta.saldo_inicial if conta.saldo_inicial is not None else Decimal(
            '0.00')

        # Buscar movimentos at\u00e9 a data_limite (exclusive)
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
