from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta


class MovimentoCrediario:
    """
    Representa um movimento de credi\u00e1rio (parcelado) de um usu\u00e1rio no sistema.
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
        Cria a tabela 'movimentos_crediario' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chaves estrangeiras para 'users', 'grupos_crediario' e 'crediarios',
        e restri\u00e7\u00f5es de unicidade.
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
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (grupo_crediario_id) REFERENCES grupos_crediario(id) ON DELETE CASCADE,
            FOREIGN KEY (crediario_id) REFERENCES crediarios(id) ON DELETE CASCADE,
            
            CHECK (num_parcelas >= 1 AND num_parcelas <= 360) -- Limite de 1 a 360 parcelas
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'movimentos_crediario' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'movimentos_crediario': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os movimentos de credi\u00e1rio de um usu\u00e1rio espec\u00edfico.
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
        Retorna um movimento de credi\u00e1rio pelo seu ID e ID do usu\u00e1rio.
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
        Calcula a \u00faltima parcela e o valor da parcela mensal.
        """
        if not isinstance(valor_total, Decimal) or not isinstance(num_parcelas, int):
            raise TypeError(
                "valor_total deve ser Decimal e num_parcelas deve ser int.")
        if num_parcelas <= 0:
            raise ValueError(
                "O n\u00famero de parcelas deve ser maior que zero.")

        # Calcular valor da parcela mensal
        valor_parcela_mensal = valor_total / Decimal(num_parcelas)
        # Arredondar para 2 casas decimais (importante para moeda)
        valor_parcela_mensal = valor_parcela_mensal.quantize(Decimal('0.01'))

        # Calcular \u00faltima parcela (primeira parcela + (num_parcelas - 1) meses)
        # Subtraimos 1 de num_parcelas porque a primeira_parcela j\u00e1 \u00e9 a primeira.
        ultima_parcela = primeira_parcela + \
            relativedelta(months=num_parcelas - 1)

        return ultima_parcela, valor_parcela_mensal

    @classmethod
    def add(cls, user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
            valor_total, num_parcelas, primeira_parcela):
        """
        Adiciona um novo movimento de credi\u00e1rio e calcula os campos derivados.
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
                return cls(result[0], user_id, grupo_crediario_id, crediario_id, data_compra,
                           descricao, valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe um movimento de credi\u00e1rio com esta combina\u00e7\u00e3o de dados para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Grupo de Credi\u00e1rio, Credi\u00e1rio ou Usu\u00e1rio n\u00e3o encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar movimento de credi\u00e1rio: {e}")
            raise

    @classmethod
    def update(cls, movimento_id, user_id, grupo_crediario_id, crediario_id, data_compra, descricao,
               valor_total, num_parcelas, primeira_parcela):
        """
        Atualiza um movimento de credi\u00e1rio existente e recalcula os campos derivados.
        """
        existing_movimento = cls.get_by_id(movimento_id, user_id)
        if not existing_movimento:
            return None  # Movimento n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

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
                return cls(movimento_id, user_id, grupo_crediario_id, crediario_id, data_compra,
                           descricao, valor_total, num_parcelas, primeira_parcela, ultima_parcela, valor_parcela_mensal)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe outro movimento de credi\u00e1rio com esta combina\u00e7\u00e3o de dados para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Grupo de Credi\u00e1rio, Credi\u00e1rio ou Usu\u00e1rio n\u00e3o encontrado."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar movimento de credi\u00e1rio: {e}")
            raise

    @classmethod
    def delete(cls, movimento_id, user_id):
        """
        Deleta um movimento de credi\u00e1rio do banco de dados.
        Retorna True em caso de sucesso, False caso contr\u00e1rio.
        """
        query = "DELETE FROM movimentos_crediario WHERE id = %s AND user_id = %s"
        params = (movimento_id, user_id)
        return execute_query(query, params, commit=True)
