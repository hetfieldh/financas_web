# routes/renda_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.renda_model import Renda  # Alterado para Renda
from functools import wraps

# Renomeado o blueprint
bp_renda = Blueprint('renda', __name__, url_prefix='/renda')


def own_renda_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio item de renda.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # O ID do item de renda vem como 'id' na rota
        renda_id = kwargs.get('id')
        if renda_id:
            renda = Renda.get_by_id(renda_id, current_user.id)
            if not renda:
                flash(
                    'Item de renda não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('renda.list_rendas'))
        return f(*args, **kwargs)
    return decorated_function


@bp_renda.route('/')
@login_required
def list_rendas():
    """
    Lista todos os itens de renda do usuário logado.
    """
    rendas = Renda.get_all_by_user(current_user.id)
    return render_template('renda/list.html', rendas=rendas)


@bp_renda.route('/add', methods=['GET', 'POST'])
@login_required
def add_renda():
    """
    Adiciona um novo item de renda para o usuário logado.
    """
    if request.method == 'POST':
        descricao = request.form['descricao']
        tipo = request.form['tipo']

        if not descricao or not tipo:
            flash('Todos os campos são obrigatórios.', 'danger')
            return render_template('renda/add.html', descricao=descricao, tipo=tipo)

        try:
            Renda.add(
                user_id=current_user.id,
                descricao=descricao,
                tipo=tipo
            )
            flash('Item de renda adicionado com sucesso!', 'success')
            return redirect(url_for('renda.list_rendas'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('renda/add.html', descricao=descricao, tipo=tipo)
        except Exception as e:
            flash(
                f'Ocorreu um erro inesperado ao adicionar o item de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar item de renda para user_id {current_user.id}: {e}", exc_info=True)
            return render_template('renda/add.html', descricao=descricao, tipo=tipo)

    return render_template('renda/add.html')


@bp_renda.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@own_renda_required
def edit_renda(id):
    """
    Edita um item de renda existente.
    """
    renda = Renda.get_by_id(id, current_user.id)

    if request.method == 'POST':
        descricao = request.form['descricao']
        tipo = request.form['tipo']

        if not descricao or not tipo:
            flash('Todos os campos são obrigatórios.', 'danger')
            renda.descricao = descricao
            renda.tipo = tipo
            return render_template('renda/edit.html', renda=renda)

        try:
            updated_renda = Renda.update(
                renda_id=renda.id,
                user_id=current_user.id,
                descricao=descricao,
                tipo=tipo
            )
            if updated_renda:
                flash('Item de renda atualizado com sucesso!', 'success')
                return redirect(url_for('renda.list_rendas'))
            else:
                flash(
                    'Erro ao atualizar item de renda. Pode ser que não tenha sido encontrado ou sem permissão.', 'danger')
        except ValueError as e:
            flash(str(e), 'danger')
            renda.descricao = descricao
            renda.tipo = tipo
            return render_template('renda/edit.html', renda=renda)
        except Exception as e:
            flash(
                f'Ocorreu um erro inesperado ao atualizar o item de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar item de renda ID {id} para user_id {current_user.id}: {e}", exc_info=True)
            renda.descricao = descricao
            renda.tipo = tipo
            return render_template('renda/edit.html', renda=renda)

    return render_template('renda/edit.html', renda=renda)


@bp_renda.route('/delete/<int:id>', methods=['POST'])
@login_required
@own_renda_required
def delete_renda(id):
    """
    Deleta um item de renda. Apenas via POST para segurança.
    """
    if Renda.delete(id, current_user.id):
        flash('Item de renda excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir item de renda.', 'danger')
    return redirect(url_for('renda.list_rendas'))
