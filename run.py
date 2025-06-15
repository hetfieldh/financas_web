from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from datetime import datetime
from werkzeug.exceptions import NotFound, InternalServerError
import logging

# Importa os MODELOS
from models.usuario_model import Usuario
from models.conta_bancaria_model import ContaBancaria
from models.transacao_bancaria_model import TransacaoBancaria
from models.movimento_bancario_model import MovimentoBancario
from models.crediario_model import Crediario
from models.grupo_crediario_model import GrupoCrediario
from models.movimento_crediario_model import MovimentoCrediario
from models.despesa_receita_model import DespesaReceita
from models.despesa_fixa_model import DespesaFixa

# Importa as ROTAS
from routes.usuario_routes import bp_usuario
from routes.conta_bancaria_routes import bp_conta_bancaria
from routes.transacao_bancaria_routes import bp_transacao_bancaria
from routes.movimento_bancario_routes import bp_movimento_bancario
from routes.crediario_routes import bp_crediario
from routes.grupo_crediario_routes import bp_grupo_crediario
from routes.movimento_crediario_routes import bp_movimento_crediario
from routes.despesa_receita_routes import bp_despesa_receita
from routes.despesa_fixa_routes import bp_despesa_fixa

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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

    # BLUEPRINT
    app.register_blueprint(bp_usuario)
    app.register_blueprint(bp_conta_bancaria)
    app.register_blueprint(bp_transacao_bancaria)
    app.register_blueprint(bp_movimento_bancario)
    app.register_blueprint(bp_crediario)
    app.register_blueprint(bp_grupo_crediario)
    app.register_blueprint(bp_movimento_crediario)
    app.register_blueprint(bp_despesa_receita)
    app.register_blueprint(bp_despesa_fixa)

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
            print("Verificando e criando tabelas no banco de dados, se necessário...")
            # Criação das tabelas por MODELS
            Usuario.create_table()
            ContaBancaria.create_table()
            TransacaoBancaria.create_table()
            MovimentoBancario.create_table()
            Crediario.create_table()
            GrupoCrediario.create_table()
            MovimentoCrediario.create_table()
            DespesaReceita.create_table()
            DespesaFixa.create_table()
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
    app.run(debug=True)  # Em produção, debug SEMPRE deve ser False.
