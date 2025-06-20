# routes/grupo_crediario_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.grupo_crediario_model import GrupoCrediario
from functools import wraps

bp_grupo_crediario = Blueprint(
    'grupo_crediario', __name__, url_prefix='/grupos_crediario')

TIPOS_GRUPO_CREDIARIO = ["Compra", "Estorno"]


def own_group_crediario_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio item de grupo de crediário.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        grupo_id = kwargs.get('grupo_id')
        if grupo_id:
            grupo = GrupoCrediario.get_by_id(grupo_id, current_user.id)
            if not grupo:
                flash(
                    'Grupo de crediário não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('grupo_crediario.list_grupos_crediario'))
        return f(*args, **kwargs)
    return decorated_function


@bp_grupo_crediario.route('/')
@login_required
def list_grupos_crediario():
    """
    Lista todos os grupos de crediário do usuário logado.
    """
    grupos = GrupoCrediario.get_all_by_user(current_user.id)
    return render_template('grupo_crediario/list.html', grupos=grupos)


@bp_grupo_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_grupo_crediario():
    """
    Adiciona um novo grupo de crediário para o usuário logado.
    """
    if request.method == 'POST':
        grupo_desc = request.form.get('grupo')
        tipo = request.form.get('tipo')

        try:
            if not grupo_desc:
                flash('O campo "Grupo" não pode ser vazio.', 'danger')
                return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)
            if tipo not in TIPOS_GRUPO_CREDIARIO:
                flash('Tipo de grupo de crediário inválido.', 'danger')
                return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)

            GrupoCrediario.add(
                user_id=current_user.id,
                grupo=grupo_desc,
                tipo=tipo
            )
            flash('Grupo de crediário adicionado com sucesso!', 'success')
            return redirect(url_for('grupo_crediario.list_grupos_crediario'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o grupo de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar grupo de crediário: {e}", exc_info=True)

    return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)


@bp_grupo_crediario.route('/edit/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
@own_group_crediario_required
def edit_grupo_crediario(grupo_id):
    """
    Edita um grupo de crediário existente.
    """
    grupo = GrupoCrediario.get_by_id(grupo_id, current_user.id)
    if not grupo:
        flash('Grupo de crediário não encontrado.', 'danger')
        return redirect(url_for('grupo_crediario.list_grupos_crediario'))

    if request.method == 'POST':
        grupo_desc = request.form.get('grupo')
        tipo = request.form.get('tipo')

        try:
            if not grupo_desc:
                flash('O campo "Grupo" não pode ser vazio.', 'danger')
                return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)
            if tipo not in TIPOS_GRUPO_CREDIARIO:
                flash('Tipo de grupo de crediário inválido.', 'danger')
                return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)

            updated_grupo = GrupoCrediario.update(
                grupo_id=grupo_id,
                user_id=current_user.id,
                grupo=grupo_desc,
                tipo=tipo
            )
            if updated_grupo:
                flash('Grupo de crediário atualizado com sucesso!', 'success')
                return redirect(url_for('grupo_crediario.list_grupos_crediario'))
            else:
                flash('Erro ao atualizar grupo de crediário.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o grupo de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar grupo de crediário ID {grupo_id}: {e}", exc_info=True)

    return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)


@bp_grupo_crediario.route('/delete/<int:grupo_id>', methods=['POST'])
@login_required
@own_group_crediario_required
def delete_grupo_crediario(grupo_id):
    """
    Deleta um grupo de crediário. Apenas via POST para segurança.
    """
    try:
        if GrupoCrediario.delete(grupo_id, current_user.id):
            flash('Grupo de crediário deletado com sucesso!', 'success')
        else:
            flash('Erro ao deletar grupo de crediário.', 'danger')

    except ValueError as e:
        flash(f'Erro: {e}', 'danger')
        current_app.logger.warning(
            f"Erro de validação ao deletar grupo de crediário ID {grupo_id} (UserID: {current_user.id}): {e}")
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao deletar o grupo de crediário: {e}', 'danger')
        current_app.logger.error(
            f"Erro inesperado ao deletar grupo de crediário ID {grupo_id} (UserID: {current_user.id}): {e}", exc_info=True)

    return redirect(url_for('grupo_crediario.list_grupos_crediario'))
