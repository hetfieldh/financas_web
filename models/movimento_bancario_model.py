from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from datetime import datetime


class MovimentoBancario:
    """
    Representa um movimento bancário (despesa ou receita) associado a uma conta
    bancária e a um tipo de transação.
    """

    def __init__(self, id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        self.id = id
        self.user_id = user_id
        self.conta_bancaria_id = conta_bancaria_id
        self.transacao_bancaria_id = transacao_bancaria_id
        self.data = data if isinstance(data, datetime) else datetime.strptime(str(data), '%Y-%m-%d')
        self.valor = float(valor)
        self.tipo = tipo  

    @staticmethod
    def create_table():
        """
        Cria a tabela 'movimentos_bancarios' no banco de dados se ela ainda não existir.
        Inclui chaves estrangeiras para 'users', 'contas_bancarias' e 'transacoes_bancarias'.
        """
        query = """
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            conta_bancaria_id INTEGER NOT NULL,
            transacao_bancaria_id INTEGER NOT NULL,
            data DATE NOT NULL,
            valor NUMERIC(15, 2) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Opções: 'Despesa', 'Receita'
            UNIQUE (user_id, conta_bancaria_id, data, valor),
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
            # Re-lança a exceção para impedir a inicialização da aplicação.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os movimentos bancários de um usuário específico,
        ordenados por data. Inclui detalhes da conta e da transação.
        """
        query = """
        SELECT
            mb.id, mb.user_id, mb.conta_bancaria_id, mb.transacao_bancaria_id, mb.data, mb.valor, mb.tipo
        FROM
            movimentos_bancarios mb
        WHERE
            mb.user_id = %s
        ORDER BY
            mb.data DESC, mb.id DESC;
        """
        rows = execute_query(query, (user_id,), fetchall=True)
        # Garante que o ID é um inteiro ao criar a instância do objeto MovimentoBancario
        return [cls(int(row[0]), *row[1:]) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, movimento_id, user_id):
        """
        Retorna um movimento bancário pelo seu ID e ID do usuário,
        garantindo que o usuário é o proprietário.
        """
        query = """
        SELECT
            id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo
        FROM
            movimentos_bancarios
        WHERE
            id = %s AND user_id = %s;
        """
        row = execute_query(query, (movimento_id, user_id), fetchone=True)
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        """
        Adiciona um novo movimento bancário ao banco de dados.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
        """
        try:
            result = execute_query(
                "INSERT INTO movimentos_bancarios (user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, conta_bancaria_id,
                 transacao_bancaria_id, data, valor, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe um movimento bancário idêntico para esta conta e data."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Conta bancária ou Transação não encontrada. Verifique os IDs fornecidos."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento bancário: {e}")
            raise

    @classmethod
    def update(cls, movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo):
        """
        Atualiza as informações de um movimento bancário existente.
        Levanta ValueError em caso de violação de unicidade ou se o movimento não for encontrado.
        """
        # Primeiro, verifica se o movimento existe e pertence ao usuário
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None  # Movimento não encontrado ou não pertence ao usuário

        try:
            query = "UPDATE movimentos_bancarios SET conta_bancaria_id = %s, transacao_bancaria_id = %s, data = %s, valor = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (conta_bancaria_id, transacao_bancaria_id,
                      data, valor, tipo, movimento_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(movimento_id, user_id, conta_bancaria_id, transacao_bancaria_id, data, valor, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro movimento bancário idêntico para esta conta e data."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar movimento bancário: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id):
        """
        Deleta um movimento bancário do banco de dados pelo seu ID e ID do usuário.
        Retorna True em caso de sucesso, False caso contrário.
        """
        # Garante que apenas o proprietário pode deletar
        query = "DELETE FROM movimentos_bancarios WHERE id = %s AND user_id = %s"
        params = (movimento_id, user_id)
        return execute_query(query, params, commit=True)
