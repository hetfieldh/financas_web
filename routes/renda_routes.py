# routes/renda_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.renda_model import Renda
from functools import wraps

bp_renda = Blueprint('renda', __name__, url_prefix='/rendas')

TIPOS_RENDA = ["Provento", "Desconto", "Benefício", "Imposto", "Outro"]


def own_renda_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    sua própria renda.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        renda_id = kwargs.get('renda_id')
        if renda_id:
            renda = Renda.get_by_id(renda_id, current_user.id)
            if not renda:
                flash(
                    'Renda não encontrada ou você não tem permissão para acessá-la.', 'danger')
                return redirect(url_for('renda.list_rendas'))
        return f(*args, **kwargs)
    return decorated_function


@bp_renda.route('/')
@login_required
def list_rendas():
    """
    Lista todos os tipos de renda do usuário logado.
    """
    rendas = Renda.get_all_by_user(current_user.id)
    return render_template('renda/list.html', rendas=rendas)


@bp_renda.route('/add', methods=['GET', 'POST'])
@login_required
def add_renda():
    """
    Adiciona um novo tipo de renda para o usuário logado.
    """
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')

        try:
            if not descricao:
                flash('O campo "Descrição" não pode ser vazio.', 'danger')
                return render_template('renda/add.html', TIPOS_RENDA=TIPOS_RENDA)
            if tipo not in TIPOS_RENDA:
                flash('Tipo de renda inválido.', 'danger')
                return render_template('renda/add.html', TIPOS_RENDA=TIPOS_RENDA)

            Renda.add(
                user_id=current_user.id,
                descricao=descricao,
                tipo=tipo
            )
            flash('Renda adicionada com sucesso!', 'success')
            return redirect(url_for('renda.list_rendas'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar a renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar renda (UserID: {current_user.id}): {e}", exc_info=True)

    return render_template('renda/add.html', TIPOS_RENDA=TIPOS_RENDA)


@bp_renda.route('/edit/<int:renda_id>', methods=['GET', 'POST'])
@login_required
@own_renda_required
def edit_renda(renda_id):
    """
    Edita um tipo de renda existente.
    """
    renda = Renda.get_by_id(renda_id, current_user.id)

    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')

        try:
            if not descricao:
                flash('O campo "Descrição" não pode ser vazio.', 'danger')
                return render_template('renda/edit.html', renda=renda, TIPOS_RENDA=TIPOS_RENDA)
            if tipo not in TIPOS_RENDA:
                flash('Tipo de renda inválido.', 'danger')
                return render_template('renda/edit.html', renda=renda, TIPOS_RENDA=TIPOS_RENDA)

            updated_renda = Renda.update(
                renda_id=renda_id,
                user_id=current_user.id,
                descricao=descricao,
                tipo=tipo
            )
            if updated_renda:
                flash('Renda atualizada com sucesso!', 'success')
                return redirect(url_for('renda.list_rendas'))
            else:
                flash('Erro ao atualizar renda.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar a renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar renda ID {renda_id} (UserID: {current_user.id}): {e}", exc_info=True)

    return render_template('renda/edit.html', renda=renda, TIPOS_RENDA=TIPOS_RENDA)


@bp_renda.route('/delete/<int:renda_id>', methods=['POST'])
@login_required
@own_renda_required
def delete_renda(renda_id):
    """
    Deleta um tipo de renda. Apenas via POST para segurança.
    """
    try:
        if Renda.delete(renda_id, current_user.id):
            flash('Renda deletada com sucesso!', 'success')
        else:
            flash(
                'Não foi possível deletar a renda. Ela pode não existir ou você não tem permissão.', 'danger')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')
        current_app.logger.warning(
            f"Erro de validação ao deletar renda ID {renda_id} (UserID: {current_user.id}): {e}")
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao deletar a renda: {e}', 'danger')
        current_app.logger.error(
            f"Erro inesperado ao deletar renda ID {renda_id} (UserID: {current_user.id}): {e}", exc_info=True)

    return redirect(url_for('renda.list_rendas'))
