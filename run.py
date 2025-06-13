from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models.usuario_model import Usuario
from database.db_manager import check_and_update_table_constraints
from routes.usuario_routes import bp_usuario
import logging
from datetime import datetime
from werkzeug.exceptions import NotFound, InternalServerError

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    """
    Cria e configura a instância da aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'usuario.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """
        Função de callback do Flask-Login para carregar um usuário dado seu ID.
        Usado para re-autenticar o usuário a cada requisição.
        """
        return Usuario.get_by_id(int(user_id))

    # Registra o Blueprint de usuário
    app.register_blueprint(bp_usuario)

    # Context processor para adicionar variáveis globais aos templates
    @app.context_processor
    def inject_global_variables():
        """
        Injeta variáveis que estarão disponíveis em todos os templates.
        Aqui, injetamos o ano atual.
        """
        return dict(
            current_year=datetime.now().year
        )

    # Hook para executar ações antes da primeira requisição
    @app.before_request
    def before_first_request_actions():
        """
        Executa uma vez antes da primeira requisição.
        Ideal para setup inicial do banco de dados.
        """
        if not hasattr(app, '_db_initialized'):
            print("Verificando e criando tabela 'users' se necessário...")
            Usuario.create_table()
            print("Verificando e atualizando constraints da tabela 'users' se necessário...")
            check_and_update_table_constraints()
            app._db_initialized = True
            # --- REMOVIDO: Bloco de criação automática do usuário admin ---
            # if not Usuario.get_by_login('admin'):
            #     print("Criando usuário administrador padrão 'admin'...")
            #     try:
            #         Usuario.add('Administrador Padrão', 'admin@financas.com', 'admin', 'adminpass', is_admin=True)
            #         print("Usuário 'admin' criado com sucesso (login: admin, senha: adminpass)")
            #     except Exception as e:
            #         print(f"Falha ao criar usuário admin padrão: {e}")
            # --- FIM DA REMOÇÃO ---

    return app

# Bloco principal para rodar a aplicação
if __name__ == '__main__':
    app = create_app()
    # MUDANÇA AQUI: Defina debug=False para testar as páginas de erro personalizadas.
    # Em produção, debug SEMPRE deve ser False.
    app.run(debug=True)
