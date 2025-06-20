# routes/crediario_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.crediario_model import Crediario
from functools import wraps
from decimal import Decimal

bp_crediario = Blueprint('crediario', __name__, url_prefix='/crediarios')

TIPOS_CREDIARIO = ["Físico", "Virtual Recorrente",
                   "Virtual Temporário", "Outro"]


def own_crediario_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio item de crediário.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        crediario_id = kwargs.get('crediario_id')
        if crediario_id:
            crediario = Crediario.get_by_id(crediario_id, current_user.id)
            if not crediario:
                flash(
                    'Item de crediário não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('crediario.list_crediarios'))
        return f(*args, **kwargs)
    return decorated_function


@bp_crediario.route('/')
@login_required
def list_crediarios():
    """
    Lista todos os itens de crediário do usuário logado.
    """
    crediarios = Crediario.get_all_by_user(current_user.id)
    return render_template('crediario/list.html', crediarios=crediarios)


@bp_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_crediario():
    """
    Adiciona um novo item de crediário para o usuário logado.
    """
    if request.method == 'POST':
        crediario_desc = request.form.get('crediario')
        tipo = request.form.get('tipo')
        final_str = request.form.get('final')
        limite_str = request.form.get('limite').replace(',', '.')

        try:
            final = int(final_str)
            limite = Decimal(limite_str)

            if not crediario_desc:
                flash('O campo "Crediário" não pode ser vazio.', 'danger')
                return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)
            if tipo not in TIPOS_CREDIARIO:
                flash('Tipo de crediário inválido.', 'danger')
                return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)

            Crediario.add(
                user_id=current_user.id,
                crediario=crediario_desc,
                tipo=tipo,
                final=final,
                limite=limite
            )
            flash('Item de crediário adicionado com sucesso!', 'success')
            return redirect(url_for('crediario.list_crediarios'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o item de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar crediário: {e}", exc_info=True)

    return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)


@bp_crediario.route('/edit/<int:crediario_id>', methods=['GET', 'POST'])
@login_required
@own_crediario_required
def edit_crediario(crediario_id):
    """
    Edita um item de crediário existente.
    """
    crediario = Crediario.get_by_id(crediario_id, current_user.id)
    if not crediario:
        flash('Item de crediário não encontrado.', 'danger')
        return redirect(url_for('crediario.list_crediarios'))

    if request.method == 'POST':
        crediario_desc = request.form.get('crediario')
        tipo = request.form.get('tipo')
        final_str = request.form.get('final')
        limite_str = request.form.get('limite').replace(',', '.')

        try:
            final = int(final_str)
            limite = Decimal(limite_str)

            if not crediario_desc:
                flash('O campo "Crediário" não pode ser vazio.', 'danger')
                return render_template('crediario/edit.html', crediario=crediario, TIPOS_CREDIARIO=TIPOS_CREDIARIO)
            if tipo not in TIPOS_CREDIARIO:
                flash('Tipo de crediário inválido.', 'danger')
                return render_template('crediario/edit.html', crediario=crediario, TIPOS_CREDIARIO=TIPOS_CREDIARIO)

            updated_crediario = Crediario.update(
                crediario_id=crediario_id,
                user_id=current_user.id,
                crediario=crediario_desc,
                tipo=tipo,
                final=final,
                limite=limite
            )
            if updated_crediario:
                flash('Item de crediário atualizado com sucesso!', 'success')
                return redirect(url_for('crediario.list_crediarios'))
            else:
                flash('Erro ao atualizar item de crediário.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o item de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar crediário ID {crediario_id}: {e}", exc_info=True)

    return render_template('crediario/edit.html', crediario=crediario, TIPOS_CREDIARIO=TIPOS_CREDIARIO)


@bp_crediario.route('/delete/<int:crediario_id>', methods=['POST'])
@login_required
@own_crediario_required
def delete_crediario(crediario_id):
    """
    Deleta um item de crediário. Apenas via POST para segurança
    """
    try:
        if Crediario.delete(crediario_id, current_user.id):
            flash('Item de crediário deletado com sucesso!', 'success')
        else:
            flash('Não foi possível deletar o item de crediário. Ele pode não existir ou você não tem permissão.', 'danger')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')
        current_app.logger.warning(
            f"Erro de validação ao deletar crediário ID {crediario_id} (UserID: {current_user.id}): {e}")
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao deletar o item de crediário: {e}', 'danger')
        current_app.logger.error(
            f"Erro inesperado ao deletar crediário ID {crediario_id} (UserID: {current_user.id}): {e}", exc_info=True)

    return redirect(url_for('crediario.list_crediarios'))
