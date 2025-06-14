from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class GrupoCrediario:
    """
    Representa um grupo de credi\u00e1rio de um usu\u00e1rio no sistema.
    """

    def __init__(self, id, user_id, grupo, tipo):
        self.id = id
        self.user_id = user_id
        self.grupo = grupo
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'grupos_crediario' no banco de dados se ela ainda n\u00e3o existir.
        Inclui chave estrangeira para 'users' e restri\u00e7\u00e3o de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS grupos_crediario (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            grupo VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Op\u00e7\u00f5es: Compra, Estorno
            
            UNIQUE (user_id, grupo, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'grupos_crediario' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CR\u00cdTICO ao criar/verificar tabela 'grupos_crediario': {e}")
            # Re-lan\u00e7a a exce\u00e7\u00e3o para impedir a inicializa\u00e7\u00e3o da aplica\u00e7\u00e3o.
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os grupos de credi\u00e1rio de um usu\u00e1rio espec\u00edfico.
        Ordena por grupo e tipo.
        """
        rows = execute_query(
            "SELECT id, user_id, grupo, tipo FROM grupos_crediario WHERE user_id = %s ORDER BY grupo, tipo",
            (user_id,),
            fetchall=True
        )
        return [cls(*row) for row in rows] if rows else []

    @classmethod
    def get_by_id(cls, grupo_id, user_id):
        """
        Retorna um grupo de credi\u00e1rio pelo seu ID e ID do usu\u00e1rio.
        """
        row = execute_query(
            "SELECT id, user_id, grupo, tipo FROM grupos_crediario WHERE id = %s AND user_id = %s",
            (grupo_id, user_id),
            fetchone=True
        )
        return cls(*row) if row else None

    @classmethod
    def add(cls, user_id, grupo, tipo):
        """
        Adiciona um novo grupo de credi\u00e1rio ao banco de dados.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou chave estrangeira.
        """
        try:
            result = execute_query(
                "INSERT INTO grupos_crediario (user_id, grupo, tipo) VALUES (%s, %s, %s) RETURNING id",
                (user_id, grupo, tipo),
                fetchone=True,
                commit=True
            )
            if result:
                return cls(result[0], user_id, grupo, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe um grupo de credi\u00e1rio com esta combina\u00e7\u00e3o de grupo e tipo para este usu\u00e1rio."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usu\u00e1rio n\u00e3o encontrado. N\u00e3o \u00e9 poss\u00edvel adicionar grupo de credi\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar grupo de credi\u00e1rio: {e}")
            raise

    @classmethod
    def update(cls, grupo_id, user_id, grupo, tipo):
        """
        Atualiza as informa\u00e7\u00f5es de um grupo de credi\u00e1rio existente.
        Levanta ValueError em caso de viola\u00e7\u00e3o de unicidade ou se o grupo n\u00e3o for encontrado.
        """
        existing_grupo = cls.get_by_id(grupo_id, user_id)
        if not existing_grupo:
            return None  # Grupo n\u00e3o encontrado ou n\u00e3o pertence ao usu\u00e1rio

        try:
            query = "UPDATE grupos_crediario SET grupo = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (grupo, tipo, grupo_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(grupo_id, user_id, grupo, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: J\u00e1 existe outro grupo de credi\u00e1rio com esta combina\u00e7\u00e3o de grupo e tipo para este usu\u00e1rio."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar grupo de credi\u00e1rio: {e}")
            raise

    @classmethod
    def delete(cls, grupo_id, user_id):
        """
        Deleta um grupo de credi\u00e1rio do banco de dados.
        Retorna True em caso de sucesso, False caso contr\u00e1rio.
        """
        query = "DELETE FROM grupos_crediario WHERE id = %s AND user_id = %s"
        params = (grupo_id, user_id)
        return execute_query(query, params, commit=True)
