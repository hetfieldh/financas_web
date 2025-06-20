# models/conta_bancaria_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal


class ContaBancaria:
    """
    Representa uma conta bancária de um usuário no sistema.
    """

    def __init__(self, id, user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite):
        self.id = id
        self.user_id = user_id
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.tipo = tipo
        self.saldo_inicial = saldo_inicial
        self.saldo_atual = saldo_atual
        self.limite = limite

    @staticmethod
    def create_table():
        """
        Cria a tabela 'contas_bancarias' no banco de dados se ela ainda não existir.
        Inclui uma chave estrangeira para a tabela 'users'.
        """
        query = """
        CREATE TABLE IF NOT EXISTS contas_bancarias (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            banco VARCHAR(255) NOT NULL,
            agencia VARCHAR(4) NOT NULL,
            conta VARCHAR(20) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            saldo_inicial NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            saldo_atual NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            limite NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            UNIQUE (user_id, banco, agencia, conta, tipo),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'contas_bancarias' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'contas_bancarias': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todas as contas bancárias de um usuário específico.
        """
        rows = execute_query(
            "SELECT id, user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite FROM contas_bancarias WHERE user_id = %s ORDER BY banco, tipo",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, conta_id, user_id):
        """
        Retorna uma conta bancária pelo seu ID e ID do usuário, garantindo que o usuário é o proprietário.
        """
        row = execute_query(
            "SELECT id, user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite FROM contas_bancarias WHERE id = %s AND user_id = %s",
            (conta_id, user_id),
            fetchone=True
        )
        if row:
            row_list = list(row)
            row_list[6] = Decimal(str(row_list[6]))
            row_list[7] = Decimal(str(row_list[7]))
            row_list[8] = Decimal(str(row_list[8]))
            return cls(*row_list)
        return None

    @classmethod
    def add(cls, user_id, banco, agencia, conta, tipo, saldo_inicial=Decimal('0.00'), saldo_atual=Decimal('0.00'), limite=Decimal('0.00')):
        """
        Adiciona uma nova conta bancária ao banco de dados.
        O saldo_atual será inicializado com o saldo_inicial fornecido.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
        """
        saldo_atual = saldo_inicial
        try:
            result = execute_query(
                "INSERT INTO contas_bancarias (user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, banco, agencia, conta, tipo,
                 saldo_inicial, saldo_atual, limite),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe uma conta bancária com esta combinação de banco, agência, conta e tipo para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar conta bancária."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar conta bancária: {e}")
            raise

    @classmethod
    def update(cls, conta_id, user_id, banco, agencia, conta, tipo, saldo_inicial, saldo_atual, limite):
        """
        Atualiza as informações de uma conta bancária existente.
        O saldo_atual NÃO é atualizado aqui diretamente, pois é gerenciado por movimentos bancários.
        Você pode ajustar o saldo_inicial e o limite.
        Levanta ValueError em caso de violação de unicidade ou se a conta não for encontrada.
        """
        existing_conta = cls.get_by_id(conta_id, user_id)
        if not existing_conta:
            return None

        try:
            query = """
                UPDATE contas_bancarias
                SET banco = %s, agencia = %s, conta = %s, tipo = %s, saldo_inicial = %s, saldo_atual = %s, limite = %s
                WHERE id = %s AND user_id = %s
            """
            params = (banco, agencia, conta, tipo, saldo_inicial, saldo_atual,
                      limite, conta_id, user_id)
            if execute_query(query, params, commit=True):
                return cls.get_by_id(conta_id, user_id)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outra conta bancária com esta combinação de banco, agência, conta e tipo para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar conta bancária: {e}")
            raise

    @classmethod
    def delete(cls, conta_id, user_id):
        """
        Deleta uma conta bancária do banco de dados pelo seu ID e ID do usuário.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM contas_bancarias WHERE id = %s AND user_id = %s"
        params = (conta_id, user_id)
        try:
            return execute_query(query, params, commit=True)
        except ForeignKeyViolation as e:
            raise ValueError(
                "Não é possível deletar esta conta bancária, pois ela possui lançamento ou vínculo com outra tabela. Remova as associações primeiro."
            ) from e
        except Exception as e:
            print(f"Erro inesperado ao deletar a conta bancária: {e}")
            raise

    @staticmethod
    def update_saldo(conta_id, user_id, valor_a_ajustar, connection=None, cursor=None):
        """
        Atualiza o saldo atual de uma conta bancária.
        Este método é projetado para ser chamado dentro de uma transação maior.

        Args:
            conta_id (int): O ID da conta bancária a ser atualizada.
            user_id (int): O ID do usuário proprietário da conta (para segurança).
            valor_a_ajustar (Decimal): O valor a ser adicionado (crédito) ou subtraído (débito)
                                       do saldo atual. Use um Decimal.
            connection (obj, optional): Objeto de conexão do banco de dados. Se fornecido,
                                        a query será executada na transação existente.
            cursor (obj, optional): Objeto de cursor do banco de dados. Se fornecido,
                                    a query será executada usando este cursor.
        Raises:
            Exception: Se ocorrer um erro durante a atualização do saldo.
        """
        query = """
            UPDATE contas_bancarias
            SET saldo_atual = saldo_atual + %s
            WHERE id = %s AND user_id = %s;
        """
        params = (valor_a_ajustar, conta_id, user_id)

        try:
            return execute_query(query, params, commit=False, connection=connection, cursor=cursor)
        except Exception as e:
            print(
                f"Erro ao ajustar saldo da conta {conta_id} (usuário {user_id}): {e}")
            raise
