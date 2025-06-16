# routes/usuario_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario_model import Usuario
from functools import wraps

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
@login_required
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
        return redirect(url_for('usuario.home'))

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        user = Usuario.get_by_login(login)
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('usuario.home'))
        else:
            flash('Login ou senha inválidos.', 'danger')
            current_app.logger.warning(
                f"Tentativa de login falha para o usuário: {login}")
    return render_template('login.html')


@bp_usuario.route('/logout')
@login_required
def logout():
    """
    Rota para logout de usuários.
    """
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('usuario.login'))


@bp_usuario.route('/usuario/list')
@login_required
@admin_required
def list_users():
    """
    Lista todos os usuários cadastrados no sistema.
    """
    users = Usuario.get_all()
    return render_template('usuario/list.html', users=users)


@bp_usuario.route('/usuario/add', methods=['GET', 'POST'])
@login_required
@admin_required
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
        is_admin = request.form.get('is_admin') == 'on'

        try:
            Usuario.add(name, email, login, password, is_admin=is_admin)
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('usuario.list_users'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Ocorreu um erro ao adicionar o usuário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar usuário: {e}", exc_info=True)

    return render_template('usuario/add.html')


@bp_usuario.route('/usuario/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
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
        new_password = request.form.get('password')
        is_admin = request.form.get(
            'is_admin') == 'on'

        try:
            updated_user = Usuario.update(
                user_id, name, email, login,
                new_password=new_password if new_password else None,
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
            current_app.logger.error(
                f"Erro ao atualizar usuário ID {user_id}: {e}", exc_info=True)

    return render_template('usuario/edit.html', user=user)


@bp_usuario.route('/usuario/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """
    Deleta um usuário do sistema. Apenas via POST para segurança.
    """
    if current_user.id == user_id:
        flash('Você não pode deletar sua própria conta através desta interface.', 'warning')
        return redirect(url_for('usuario.list_users'))

    if Usuario.delete(user_id):
        flash('Usuário deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar usuário.', 'danger')
    return redirect(url_for('usuario.list_users'))
