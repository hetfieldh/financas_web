# models/grupo_crediario_model.py

from database.db_manager import execute_query
from psycopg.errors import UniqueViolation, ForeignKeyViolation


class GrupoCrediario:
    """
    Representa um grupo de crediário de um usuário no sistema.
    """

    def __init__(self, id, user_id, grupo, tipo):
        self.id = id
        self.user_id = user_id
        self.grupo = grupo
        self.tipo = tipo

    @staticmethod
    def create_table():
        """
        Cria a tabela 'grupos_crediario' no banco de dados se ela ainda não existir.
        Inclui chave estrangeira para 'users' e restrição de unicidade.
        """
        query = """
        CREATE TABLE IF NOT EXISTS grupos_crediario (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            grupo VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL, -- Opções: Compra, Estorno
            
            UNIQUE (user_id, grupo, tipo),
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """
        try:
            execute_query(query, commit=True)
            print("Tabela 'grupos_crediario' verificada/criada com sucesso.")
        except Exception as e:
            print(
                f"ERRO CRÍTICO ao criar/verificar tabela 'grupos_crediario': {e}")
            raise

    @classmethod
    def get_all_by_user(cls, user_id):
        """
        Retorna uma lista de todos os grupos de crediário de um usuário específico.
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
        Retorna um grupo de crediário pelo seu ID e ID do usuário.
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
        Adiciona um novo grupo de crediário ao banco de dados.
        Levanta ValueError em caso de violação de unicidade ou chave estrangeira.
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
                "Erro: Já existe um grupo de crediário com esta combinação de grupo e tipo para este usuário."
            ) from e
        except ForeignKeyViolation as e:
            raise ValueError(
                "Erro: Usuário não encontrado. Não é possível adicionar grupo de crediário."
            ) from e
        except Exception as e:
            print(f"Erro ao adicionar grupo de crediário: {e}")
            raise

    @classmethod
    def update(cls, grupo_id, user_id, grupo, tipo):
        """
        Atualiza as informações de um grupo de crediário existente.
        Levanta ValueError em caso de violação de unicidade ou se o grupo não for encontrado.
        """
        existing_grupo = cls.get_by_id(grupo_id, user_id)
        if not existing_grupo:
            return None

        try:
            query = "UPDATE grupos_crediario SET grupo = %s, tipo = %s WHERE id = %s AND user_id = %s"
            params = (grupo, tipo, grupo_id, user_id)
            if execute_query(query, params, commit=True):
                return cls(grupo_id, user_id, grupo, tipo)
            return None
        except UniqueViolation as e:
            raise ValueError(
                "Erro: Já existe outro grupo de crediário com esta combinação de grupo e tipo para este usuário."
            ) from e
        except Exception as e:
            print(f"Erro ao atualizar grupo de crediário: {e}")
            raise

    @classmethod
    def delete(cls, grupo_id, user_id):
        """
        Deleta um grupo de crediário do banco de dados.
        Retorna True em caso de sucesso, False caso contrário.
        """
        query = "DELETE FROM grupos_crediario WHERE id = %s AND user_id = %s"
        params = (grupo_id, user_id)
        try:
            return execute_query(query, params, commit=True)
        except ForeignKeyViolation as e:
            raise ValueError(
                "Não é possível deletar este grupo de crediário, pois ele possui lançamento ou vínculo com outra tabela. Remova as associações primeiro."
            ) from e
        except Exception as e:
            print(f"Erro inesperado ao deletar grupo de crediário: {e}")
            raise
