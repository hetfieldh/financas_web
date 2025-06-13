from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario_model import Usuario
from functools import wraps

# Cria um Blueprint para organizar as rotas relacionadas a usuários
bp_usuario = Blueprint('usuario', __name__)

def admin_required(f):
    """
    Decorador personalizado para exigir que o usuário logado seja um administrador.
    Redireciona para a home se o usuário não for administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('usuario.home'))
        return f(*args, **kwargs)
    return decorated_function

@bp_usuario.route('/')
@login_required # Garante que apenas usuários logados possam acessar a home
def home():
    """
    Rota da página inicial após o login.
    """
    return render_template('home.html', user=current_user)

@bp_usuario.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para o login de usuários.
    GET: Exibe o formulário de login.
    POST: Processa a submissão do formulário de login.
    """
    if current_user.is_authenticated:
        # Se o usuário já estiver logado, redireciona para a página inicial.
        return redirect(url_for('usuario.home'))

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        user = Usuario.get_by_login(login)
        if user and user.check_password(password):
            # Autentica o usuário com Flask-Login
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            # Redireciona para a página que o usuário tentou acessar, ou para a home.
            next_page = request.args.get('next')
            return redirect(next_page or url_for('usuario.home'))
        else:
            flash('Login ou senha inválidos.', 'danger')
            current_app.logger.warning(f"Tentativa de login falha para o usuário: {login}")
    # Renderiza o template de login para GET ou em caso de falha de POST
    return render_template('login.html')

@bp_usuario.route('/logout')
@login_required # Apenas usuários logados podem fazer logout
def logout():
    """
    Rota para logout de usuários.
    """
    logout_user() # Desloga o usuário
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('usuario.login')) # Redireciona para a página de login

@bp_usuario.route('/usuario/list')
@login_required
@admin_required # Apenas administradores podem listar usuários
def list_users():
    """
    Lista todos os usuários cadastrados no sistema.
    """
    users = Usuario.get_all()
    return render_template('usuario/list.html', users=users)

@bp_usuario.route('/usuario/add', methods=['GET', 'POST'])
@login_required
@admin_required # Apenas administradores podem adicionar usuários
def add_user():
    """
    Adiciona um novo usuário ao sistema.
    GET: Exibe o formulário de adição.
    POST: Processa a submissão do formulário.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        login = request.form.get('login')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on' # Checkbox retorna 'on' se marcado

        try:
            Usuario.add(name, email, login, password, is_admin=is_admin)
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('usuario.list_users'))
        except ValueError as e:
            # Captura erros de violação de unicidade do modelo.
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Ocorreu um erro ao adicionar o usuário: {e}', 'danger')
            current_app.logger.error(f"Erro ao adicionar usuário: {e}", exc_info=True)

    return render_template('usuario/add.html')

@bp_usuario.route('/usuario/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required # Apenas administradores podem editar usuários
def edit_user(user_id):
    """
    Edita um usuário existente.
    GET: Exibe o formulário de edição pré-preenchido.
    POST: Processa a submissão do formulário de edição.
    """
    user = Usuario.get_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuario.list_users'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        login = request.form.get('login')
        new_password = request.form.get('password') # Pode ser vazio se não houver mudança de senha
        is_admin = request.form.get('is_admin') == 'on' # Checkbox retorna 'on'

        try:
            updated_user = Usuario.update(
                user_id, name, email, login,
                new_password=new_password if new_password else None, # Passa None se a senha não for alterada
                is_admin=is_admin
            )
            if updated_user:
                flash('Usuário atualizado com sucesso!', 'success')
                return redirect(url_for('usuario.list_users'))
            else:
                flash('Erro ao atualizar usuário.', 'danger')
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Ocorreu um erro ao atualizar o usuário: {e}', 'danger')
            current_app.logger.error(f"Erro ao atualizar usuário ID {user_id}: {e}", exc_info=True)

    # Para GET request ou em caso de erro no POST, renderiza o formulário com os dados atuais
    return render_template('usuario/edit.html', user=user)

@bp_usuario.route('/usuario/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required # Apenas administradores podem deletar usuários
def delete_user(user_id):
    """
    Deleta um usuário do sistema. Apenas via POST para segurança.
    """
    # Previne que um admin tente deletar a si mesmo (opcional, mas boa prática)
    if current_user.id == user_id:
        flash('Você não pode deletar sua própria conta através desta interface.', 'warning')
        return redirect(url_for('usuario.list_users'))

    if Usuario.delete(user_id):
        flash('Usuário deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar usuário.', 'danger')
    return redirect(url_for('usuario.list_users'))

