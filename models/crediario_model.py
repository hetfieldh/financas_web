from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation
# Importa o tipo Decimal para c\u00e1lculos monet\u00e1rios precisos
from decimal import Decimal


class Crediario:
    """
    Representa um item de credi\u00e1rio de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, crediario, tipo, final, limite):
        self.id = id
        self.user_id = user_id
        self.crediario = crediario
        self.tipo = tipo
        self.final = final
        self.limite = limite

    @staticmethod
    def create_table():
        """
        Cria a tabela 'crediarios' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chaves estrangeiras para 'users' e restri\u00e7\u00f5es de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS crediarios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            crediario VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            final INTEGER NOT NULL,
            limite NUMERIC(15, 2) NOT NULL,
            
            UNIQUE (user_id, crediario, tipo, final),
            UNIQUE (user_id, crediario, final),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'crediarios' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'crediarios': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os itens de credi\u00e1rio de um usu\u00e1rio espec\u00edfico.
        """
        rows = execute_query(
            "SELECT id, user_id, crediario, tipo, final, limite FROM crediarios WHERE user_id = %s ORDER BY crediario, final",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, crediario_id, user_id):
        """
        Retorna um item de credi\u00e1rio pelo seu ID e ID do usu\u00e1rio.
        """
        row = execute_query(
            "SELECT id, user_id, crediario, tipo, final, limite FROM crediarios WHERE id = %s AND user_id = %s",
            (crediario_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, crediario, tipo, final, limite):
        """
        Adiciona um novo item de credi\u00e1rio ao banco de dados.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou chave estrangeira.
        """
        try:
            # Valida\u00e7\u00e3o do campo 'final'
            if not (0 <= final <= 9999):  # Supondo que "m\u00e1x 4 caracteres" significa 0-9999
                raise ValueError(
                    "O campo 'Final' deve ser um n\u00famero inteiro entre 0 e 9999.")

            result = execute_query(
                "INSERT INTO crediarios (user_id, crediario, tipo, final, limite) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, crediario, tipo, final, limite),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, crediario, tipo, final, limite)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe um item de credi\u00e1rio com esta combina\u00e7\u00e3o para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usu\u00e1rio n\u00e3o encontrado. N\u00e3o \u00e9 poss\u00edvel adicionar credi\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar credi\u00e1rio: {e}")
            raise

    @classmethod
    def update(cls, crediario_id, user_id, crediario, tipo, final, limite):
        """
        Atualiza as informa\u00e7\u00f5es de um item de credi\u00e1rio existente.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou se o credi\u00e1rio n\u00e3o for encontrado.
        """
        existing_crediario = cls.get_by_id(crediario_id, user_id)
        if not existing_crediario:
            return None  # Credi\u00e1rio n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        try:
            # Valida\u00e7\u00e3o do campo 'final'
            if not (0 <= final <= 9999):
                raise ValueError(
                    "O campo 'Final' deve ser um n\u00famero inteiro entre 0 e 9999.")

            query = "UPDATE crediarios SET crediario = %s, tipo = %s, final = %s, limite = %s WHERE id = %s AND user_id = %s"
            params = (crediario, tipo, final, limite, crediario_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(crediario_id, user_id, crediario, tipo, final, limite)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe outro item de credi\u00e1rio com esta combina\u00e7\u00e3o para este usu\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar credi\u00e1rio: {e}")
            raise

    @classmethod
    def delete(cls, crediario_id, user_id):
        """
        Deleta um item de credi\u00e1rio do banco de dados.
        Retorna True em caso de sucesso, False caso contr\u00e1rio.
        """
        query = "DELETE FROM crediarios WHERE id = %s AND user_id = %s"
        params = (crediario_id, user_id)
        return execute_query(query, params, commit=True)
