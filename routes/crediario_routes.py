from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.crediario_model import Crediario
from functools import wraps
from decimal import Decimal

# Cria um Blueprint para organizar as rotas relacionadas a credi\u00e1rios
bp_crediario = Blueprint('crediario', __name__, url_prefix='/crediarios')

# Defini\u00e7\u00f5es de tipos de credi\u00e1rio para o formul\u00e1rio
TIPOS_CREDIARIO = ["F\u00edsico", "Virtual Recorrente",
                   "Virtual Tempor\u00e1rio", "Outro"]


def own_crediario_required(f):
    """
    Decorador personalizado para garantir que o usu\u00e1rio est\u00e1 acessando ou modificando
    seu pr\u00f3prio item de credi\u00e1rio.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        crediario_id = kwargs.get('crediario_id')
        if crediario_id:
            crediario = Crediario.get_by_id(crediario_id, current_user.id)
            if not crediario:
                flash('Item de credi\u00e1rio n\u00e3o encontrado ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-lo.', 'danger')
                return redirect(url_for('crediario.list_crediarios'))
        return f(*args, **kwargs)
    return decorated_function


@bp_crediario.route('/')
@login_required
def list_crediarios():
    """
    Lista todos os itens de credi\u00e1rio do usu\u00e1rio logado.
    """
    crediarios = Crediario.get_all_by_user(current_user.id)
    return render_template('crediario/list.html', crediarios=crediarios)


@bp_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_crediario():
    """
    Adiciona um novo item de credi\u00e1rio para o usu\u00e1rio logado.
    """
    if request.method == 'POST':
        # Renomeado para evitar conflito com 'crediario' objeto
        crediario_desc = request.form.get('crediario')
        tipo = request.form.get('tipo')
        final_str = request.form.get('final')
        limite_str = request.form.get('limite').replace(
            ',', '.')  # Substitui v\u00edrgula por ponto

        try:
            final = int(final_str)
            limite = Decimal(limite_str)

            # Valida\u00e7\u00f5es adicionais
            if not crediario_desc:
                flash('O campo "Credi\u00e1rio" n\u00e3o pode ser vazio.', 'danger')
                return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)
            if tipo not in TIPOS_CREDIARIO:
                flash('Tipo de credi\u00e1rio inv\u00e1lido.', 'danger')
                return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)

            Crediario.add(
                user_id=current_user.id,
                crediario=crediario_desc,
                tipo=tipo,
                final=final,
                limite=limite
            )
            flash('Item de credi\u00e1rio adicionado com sucesso!', 'success')
            return redirect(url_for('crediario.list_crediarios'))
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o item de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar credi\u00e1rio: {e}", exc_info=True)

    return render_template('crediario/add.html', TIPOS_CREDIARIO=TIPOS_CREDIARIO)


@bp_crediario.route('/edit/<int:crediario_id>', methods=['GET', 'POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 edita seus pr\u00f3prios credi\u00e1rios
@own_crediario_required
def edit_crediario(crediario_id):
    """
    Edita um item de credi\u00e1rio existente.
    """
    crediario = Crediario.get_by_id(crediario_id, current_user.id)
    if not crediario:
        flash('Item de credi\u00e1rio n\u00e3o encontrado.', 'danger')
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
                flash('O campo "Credi\u00e1rio" n\u00e3o pode ser vazio.', 'danger')
                return render_template('crediario/edit.html', crediario=crediario, TIPOS_CREDIARIO=TIPOS_CREDIARIO)
            if tipo not in TIPOS_CREDIARIO:
                flash('Tipo de credi\u00e1rio inv\u00e1lido.', 'danger')
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
                flash('Item de credi\u00e1rio atualizado com sucesso!', 'success')
                return redirect(url_for('crediario.list_crediarios'))
            else:
                flash('Erro ao atualizar item de credi\u00e1rio.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o item de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar credi\u00e1rio ID {crediario_id}: {e}", exc_info=True)

    return render_template('crediario/edit.html', crediario=crediario, TIPOS_CREDIARIO=TIPOS_CREDIARIO)


@bp_crediario.route('/delete/<int:crediario_id>', methods=['POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 deleta seus pr\u00f3prios credi\u00e1rios
@own_crediario_required
def delete_crediario(crediario_id):
    """
    Deleta um item de credi\u00e1rio. Apenas via POST para seguran\u00e7a.
    """
    if Crediario.delete(crediario_id, current_user.id):
        flash('Item de credi\u00e1rio deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar item de credi\u00e1rio.', 'danger')
    return redirect(url_for('crediario.list_crediarios'))
