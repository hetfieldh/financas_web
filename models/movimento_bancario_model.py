from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from datetime import datetime, date
from decimal import Decimal
# Importado para acessar os m\u00e9todos de atualiza\u00e7\u00e3o de conta
from models.conta_bancaria_model import ContaBancaria


class MovimentoBancario:
    """
    Representa um movimento banc\u00e1rio (receita ou despesa) de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        self.id = id
        self.user_id = user_id
        self.conta_bancaria_id = conta_bancaria_id
        self.transacao_bancaria_id = transacao_bancaria_id
        self.data = data
        self.valor = valor
        self.tipo = tipo  # "Receita" ou "Despesa"

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_bancarios' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chaves estrangeiras para 'users', 'contas_bancarias' e 'transacoes_bancarias'.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            conta_bancaria_id INTEGER NOT NULL,
            transacao_bancaria_id INTEGER NOT NULL,
            data DATE NOT NULL,
            valor NUMERIC(15, 2) NOT NULL, -- Valores monet\u00e1rios como NUMERIC com 2 casas decimais
            tipo VARCHAR(50) NOT NULL, -- "Receita" ou "Despesa"
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
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo FROM movimentos_bancarios WHERE user_id = %s ORDER BY data DESC",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento banc\u00e1rio pelo seu ID e ID do usu\u00e1rio, garantindo que o usu\u00e1rio \u00e9 o propriet\u00e1rio.
        """
        row = execute_query(
            "SELECT id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo FROM movimentos_bancarios WHERE id = %s AND user_id = %s",
            (movimento_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        """
        Adiciona um novo movimento banc\u00e1rio ao banco de dados e atualiza o saldo da conta,
        verificando o limite da conta antes da execu\u00e7\u00e3o.
        """
        try:
            conta_afetada = ContaBancaria.get_by_id(conta_bancaria_id, user_id)
            if not conta_afetada:
                raise ValueError("Conta banc\u00e1ria n\u00e3o encontrada.")

            # Calcular o saldo projetado ap\u00f3s a transa\u00e7\u00e3o
            projected_saldo = conta_afetada.saldo_atual
            if tipo == 'Receita':
                projected_saldo += abs(valor)
            elif tipo == 'Despesa':
                # Para despesa, subtra\u00edmos o valor absoluto
                projected_saldo -= abs(valor)

            # Verificar se o saldo projetado excede o limite (considerando limite como valor positivo)
            # A conta pode ir at\u00e9 -limite. Ex: limite 1000, pode ir at\u00e9 -1000.
            # Usar abs(limite) para garantir que limite seja tratado como positivo
            if projected_saldo < -abs(conta_afetada.limite):
                raise ValueError(
                    f"Movimento excederia o limite da conta banc\u00e1ria. "
                    f"Saldo projetado: R${projected_saldo:.2f}, Limite: R${conta_afetada.limite:.2f}."
                )

            # Executar todas as opera\u00e7\u00f5es de banco de dados dentro de uma \u00fanica transa\u00e7\u00e3o
            # Import localmente para evitar problemas de depend\u00eancia circular
            from database.db_manager import get_db_cursor
            with get_db_cursor(commit=True) as cursor:
                # 1. Inserir o novo movimento
                cursor.execute(
                    "INSERT INTO movimentos_bancarios (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (user_id, conta_bancaria_id,
                     transacao_bancaria_id, data, valor, tipo)
                )
                movimento_id = cursor.fetchone()[0]

                # 2. Atualizar o saldo da conta banc\u00e1ria
                cursor.execute(
                    "UPDATE contas_bancarias SET saldo_atual = %s WHERE id = %s AND user_id = %s",
                    (projected_saldo, conta_afetada.id, user_id)
                )

            return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Conta banc\u00e1ria ou transa\u00e7\u00e3o n\u00e3o encontrada. N\u00e3o \u00e9 poss\u00edvel adicionar movimento."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento banc\u00e1rio: {e}")
            raise  # Re-lan\u00e7a outras exce\u00e7\u00f5es.

    @classmethod
    def update(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        """
        Atualiza um movimento banc\u00e1rio existente e ajusta o saldo da conta,
        verificando o limite da conta antes da execu\u00e7\u00e3o.
        """
        original_movimento = cls.get_by_id(movimento_id, user_id)
        if not original_movimento:
            return None  # Movimento n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        try:
            # Obter as contas envolvidas
            original_conta = ContaBancaria.get_by_id(
                original_movimento.conta_bancaria_id, user_id)
            if not original_conta:
                raise ValueError(
                    "Conta banc\u00e1ria original do movimento n\u00e3o encontrada.")

            nova_conta = ContaBancaria.get_by_id(conta_bancaria_id, user_id)
            if not nova_conta:
                raise ValueError(
                    "Conta banc\u00e1ria de destino n\u00e3o encontrada.")

            # Calcular o saldo da conta original AP\u00d3S reverter o movimento antigo
            temp_saldo_original_conta = original_conta.saldo_atual
            if original_movimento.tipo == 'Receita':
                temp_saldo_original_conta -= abs(original_movimento.valor)
            elif original_movimento.tipo == 'Despesa':
                temp_saldo_original_conta += abs(original_movimento.valor)

            # Calcular o saldo projetado para a CONTA DE DESTINO (nova_conta)
            projected_saldo_nova_conta = nova_conta.saldo_atual
            # Se a conta de destino for a mesma que a original, usamos o saldo tempor\u00e1rio como base
            if original_movimento.conta_bancaria_id == conta_bancaria_id:
                projected_saldo_nova_conta = temp_saldo_original_conta

            if tipo == 'Receita':
                projected_saldo_nova_conta += abs(valor)
            elif tipo == 'Despesa':
                projected_saldo_nova_conta -= abs(valor)

            # Verificar o limite da CONTA DE DESTINO antes de qualquer modifica\u00e7\u00e3o no DB
            if projected_saldo_nova_conta < -abs(nova_conta.limite):
                raise ValueError(
                    f"Movimento atualizado excederia o limite da conta banc\u00e1ria. "
                    f"Saldo projetado: R${projected_saldo_nova_conta:.2f}, Limite: R${nova_conta.limite:.2f}."
                )

            # Executar todas as opera\u00e7\u00f5es de banco de dados dentro de uma \u00fanica transa\u00e7\u00e3o
            from database.db_manager import get_db_cursor  # Import localmente
            with get_db_cursor(commit=True) as cursor:
                # 1. Atualizar o movimento
                query_movimento = "UPDATE movimentos_bancarios SET conta_bancaria_id = %s, transacao_bancaria_id = %s, data = %s, valor = %s, tipo = %s WHERE id = %s AND user_id = %s"
                params_movimento = (
                    conta_bancaria_id, transacao_bancaria_id, data, valor, tipo, movimento_id, user_id)
                cursor.execute(query_movimento, params_movimento)

                # 2. Atualizar o saldo da conta ORIGINAL (se mudou ou se o saldo dela foi alterado)
                if original_movimento.conta_bancaria_id != conta_bancaria_id:
                    # Se a conta mudou, atualizamos o saldo da conta antiga com o saldo revertido
                    cursor.execute(
                        "UPDATE contas_bancarias SET saldo_atual = %s WHERE id = %s AND user_id = %s",
                        (temp_saldo_original_conta, original_conta.id, user_id)
                    )

                # 3. Atualizar o saldo da NOVA conta (ou a mesma conta, com o saldo projetado final)
                cursor.execute(
                    "UPDATE contas_bancarias SET saldo_atual = %s WHERE id = %s AND user_id = %s",
                    (projected_saldo_nova_conta, nova_conta.id, user_id)
                )

            return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
        except ForeignKeyViolation as e:
            # CORREÇÃO: Alinhamento da cláusula except
            raise ValueError(
                "Erro: Conta banc\u00e1ria ou transa\u00e7\u00e3o n\u00e3o encontrada. N\u00e3o \u00e9 poss\u00edvel atualizar movimento."
            ) from e
        except Exception as e:
            # CORREÇÃO: Alinhamento da cláusula except
            print(f"Erro ao atualizar movimento banc\u00e1rio: {e}")
            raise  # Re-lan\u00e7a outras exce\u00e7\u00f5es.

    @classmethod
    def delete(cls, movimento_id, user_id):
        """
        Deleta um movimento banc\u00e1rio e reverte seu impacto no saldo da conta,
        tudo dentro de uma transa\u00e7\u00e3o at\u00f3mica.
        """
        movimento_a_deletar = cls.get_by_id(movimento_id, user_id)
        if not movimento_a_deletar:
            return False  # Movimento n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        # Adicionado bloco try para o m\u00e9todo delete
        try:
            conta_afetada = ContaBancaria.get_by_id(
                movimento_a_deletar.conta_bancaria_id, user_id)
            if not conta_afetada:
                raise ValueError(
                    "Conta banc\u00e1ria afetada pelo movimento a ser deletado n\u00e3o encontrada.")

            # Calcular o saldo da conta ap\u00f3s reverter o movimento
            projected_saldo_after_revert = conta_afetada.saldo_atual
            if movimento_a_deletar.tipo == 'Receita':
                # Reverte a receita (subtrai)
                projected_saldo_after_revert -= abs(movimento_a_deletar.valor)
            elif movimento_a_deletar.tipo == 'Despesa':
                # Reverte a despesa (soma)
                projected_saldo_after_revert += abs(movimento_a_deletar.valor)

            # Executar todas as opera\u00e7\u00f5es de banco de dados dentro de uma \u00fanica transa\u00e7\u00e3o
            from database.db_manager import get_db_cursor  # Import localmente
            with get_db_cursor(commit=True) as cursor:
                # 1. Deletar movimento
                cursor.execute(
                    "DELETE FROM movimentos_bancarios WHERE id = %s AND user_id = %s", (movimento_id, user_id))

                # 2. Atualizar saldo da conta afetada
                cursor.execute(
                    "UPDATE contas_bancarias SET saldo_atual = %s WHERE id = %s AND user_id = %s",
                    (projected_saldo_after_revert, conta_afetada.id, user_id)
                )
            return True
        except Exception as e:
            print(f"Erro ao deletar movimento banc\u00e1rio: {e}")
            raise
