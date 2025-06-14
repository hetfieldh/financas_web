from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.grupo_crediario_model import GrupoCrediario
from functools import wraps

# Cria um Blueprint para organizar as rotas relacionadas a grupos de credi\u00e1rio
bp_grupo_crediario = Blueprint(
    'grupo_crediario', __name__, url_prefix='/grupos_crediario')

# Defini\u00e7\u00f5es de tipos de grupo de credi\u00e1rio para o formul\u00e1rio
TIPOS_GRUPO_CREDIARIO = ["Compra", "Estorno"]


def own_group_crediario_required(f):
    """
    Decorador personalizado para garantir que o usu\u00e1rio est\u00e1 acessando ou modificando
    seu pr\u00f3prio item de grupo de credi\u00e1rio.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        grupo_id = kwargs.get('grupo_id')
        if grupo_id:
            grupo = GrupoCrediario.get_by_id(grupo_id, current_user.id)
            if not grupo:
                flash('Grupo de credi\u00e1rio n\u00e3o encontrado ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-lo.', 'danger')
                return redirect(url_for('grupo_crediario.list_grupos_crediario'))
        return f(*args, **kwargs)
    return decorated_function


@bp_grupo_crediario.route('/')
@login_required
def list_grupos_crediario():
    """
    Lista todos os grupos de credi\u00e1rio do usu\u00e1rio logado.
    """
    grupos = GrupoCrediario.get_all_by_user(current_user.id)
    return render_template('grupo_crediario/list.html', grupos=grupos)


@bp_grupo_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_grupo_crediario():
    """
    Adiciona um novo grupo de credi\u00e1rio para o usu\u00e1rio logado.
    """
    if request.method == 'POST':
        # Renomeado para evitar conflito com 'grupo' objeto
        grupo_desc = request.form.get('grupo')
        tipo = request.form.get('tipo')

        try:
            # Valida\u00e7\u00f5es adicionais
            if not grupo_desc:
                flash('O campo "Grupo" n\u00e3o pode ser vazio.', 'danger')
                return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)
            if tipo not in TIPOS_GRUPO_CREDIARIO:
                flash('Tipo de grupo de credi\u00e1rio inv\u00e1lido.', 'danger')
                return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)

            GrupoCrediario.add(
                user_id=current_user.id,
                grupo=grupo_desc,
                tipo=tipo
            )
            flash('Grupo de credi\u00e1rio adicionado com sucesso!', 'success')
            return redirect(url_for('grupo_crediario.list_grupos_crediario'))
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o grupo de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar grupo de credi\u00e1rio: {e}", exc_info=True)

    return render_template('grupo_crediario/add.html', TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)


@bp_grupo_crediario.route('/edit/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 edita seus pr\u00f3prios grupos de credi\u00e1rio
@own_group_crediario_required
def edit_grupo_crediario(grupo_id):
    """
    Edita um grupo de credi\u00e1rio existente.
    """
    grupo = GrupoCrediario.get_by_id(grupo_id, current_user.id)
    if not grupo:
        flash('Grupo de credi\u00e1rio n\u00e3o encontrado.', 'danger')
        return redirect(url_for('grupo_crediario.list_grupos_crediario'))

    if request.method == 'POST':
        grupo_desc = request.form.get('grupo')
        tipo = request.form.get('tipo')

        try:
            if not grupo_desc:
                flash('O campo "Grupo" n\u00e3o pode ser vazio.', 'danger')
                return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)
            if tipo not in TIPOS_GRUPO_CREDIARIO:
                flash('Tipo de grupo de credi\u00e1rio inv\u00e1lido.', 'danger')
                return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)

            updated_grupo = GrupoCrediario.update(
                grupo_id=grupo_id,
                user_id=current_user.id,
                grupo=grupo_desc,
                tipo=tipo
            )
            if updated_grupo:
                flash('Grupo de credi\u00e1rio atualizado com sucesso!', 'success')
                return redirect(url_for('grupo_crediario.list_grupos_crediario'))
            else:
                flash('Erro ao atualizar grupo de credi\u00e1rio.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o grupo de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar grupo de credi\u00e1rio ID {grupo_id}: {e}", exc_info=True)

    return render_template('grupo_crediario/edit.html', grupo=grupo, TIPOS_GRUPO_CREDIARIO=TIPOS_GRUPO_CREDIARIO)


@bp_grupo_crediario.route('/delete/<int:grupo_id>', methods=['POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 deleta seus pr\u00f3prios grupos de credi\u00e1rio
@own_group_crediario_required
def delete_grupo_crediario(grupo_id):
    """
    Deleta um grupo de credi\u00e1rio. Apenas via POST para seguran\u00e7a.
    """
    if GrupoCrediario.delete(grupo_id, current_user.id):
        flash('Grupo de credi\u00e1rio deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar grupo de credi\u00e1rio.', 'danger')
    return redirect(url_for('grupo_crediario.list_grupos_crediario'))
