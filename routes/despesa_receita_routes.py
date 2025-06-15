from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.despesa_receita_model import DespesaReceita
from functools import wraps

# Cria um Blueprint para organizar as rotas relacionadas a despesas/receitas
bp_despesa_receita = Blueprint(
    'despesa_receita', __name__, url_prefix='/despesas_receitas')

# Defini\u00e7\u00f5es de tipos de despesa/receita para o formul\u00e1rio
TIPOS_DESPESA_RECEITA = ["Receita", "Despesa"]


def own_expense_revenue_required(f):
    """
    Decorador personalizado para garantir que o usu\u00e1rio est\u00e1 acessando ou modificando
    seu pr\u00f3prio item de despesa/receita.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        item_id = kwargs.get('item_id')
        if item_id:
            item = DespesaReceita.get_by_id(item_id, current_user.id)
            if not item:
                flash('Item de despesa/receita n\u00e3o encontrado ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-lo.', 'danger')
                return redirect(url_for('despesa_receita.list_despesas_receitas'))
        return f(*args, **kwargs)
    return decorated_function


@bp_despesa_receita.route('/')
@login_required
def list_despesas_receitas():
    """
    Lista todos os itens de despesa/receita do usu\u00e1rio logado.
    """
    items = DespesaReceita.get_all_by_user(current_user.id)
    return render_template('despesa_receita/list.html', items=items)


@bp_despesa_receita.route('/add', methods=['GET', 'POST'])
@login_required
def add_despesa_receita():
    """
    Adiciona um novo item de despesa/receita para o usu\u00e1rio logado.
    """
    if request.method == 'POST':
        despesa_receita_desc = request.form.get('despesa_receita')
        tipo = request.form.get('tipo')

        try:
            # Valida\u00e7\u00f5es adicionais
            if not despesa_receita_desc:
                flash('O campo "Descri\u00e7\u00e3o" n\u00e3o pode ser vazio.', 'danger')
                return render_template('despesa_receita/add.html', TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)
            if tipo not in TIPOS_DESPESA_RECEITA:
                flash('Tipo de despesa/receita inv\u00e1lido.', 'danger')
                return render_template('despesa_receita/add.html', TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)

            DespesaReceita.add(
                user_id=current_user.id,
                despesa_receita=despesa_receita_desc,
                tipo=tipo
            )
            flash('Item de despesa/receita adicionado com sucesso!', 'success')
            return redirect(url_for('despesa_receita.list_despesas_receitas'))
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o item de despesa/receita: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar despesa/receita: {e}", exc_info=True)

    return render_template('despesa_receita/add.html', TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)


@bp_despesa_receita.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 edita seus pr\u00f3prios itens
@own_expense_revenue_required
def edit_despesa_receita(item_id):
    """
    Edita um item de despesa/receita existente.
    """
    item = DespesaReceita.get_by_id(item_id, current_user.id)
    if not item:
        flash('Item de despesa/receita n\u00e3o encontrado.', 'danger')
        return redirect(url_for('despesa_receita.list_despesas_receitas'))

    if request.method == 'POST':
        despesa_receita_desc = request.form.get('despesa_receita')
        tipo = request.form.get('tipo')

        try:
            if not despesa_receita_desc:
                flash('O campo "Descri\u00e7\u00e3o" n\u00e3o pode ser vazio.', 'danger')
                return render_template('despesa_receita/edit.html', item=item, TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)
            if tipo not in TIPOS_DESPESA_RECEITA:
                flash('Tipo de despesa/receita inv\u00e1lido.', 'danger')
                return render_template('despesa_receita/edit.html', item=item, TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)

            updated_item = DespesaReceita.update(
                item_id=item_id,
                user_id=current_user.id,
                despesa_receita=despesa_receita_desc,
                tipo=tipo
            )
            if updated_item:
                flash('Item de despesa/receita atualizado com sucesso!', 'success')
                return redirect(url_for('despesa_receita.list_despesas_receitas'))
            else:
                flash('Erro ao atualizar item de despesa/receita.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o item de despesa/receita: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar despesa/receita ID {item_id}: {e}", exc_info=True)

    return render_template('despesa_receita/edit.html', item=item, TIPOS_DESPESA_RECEITA=TIPOS_DESPESA_RECEITA)


@bp_despesa_receita.route('/delete/<int:item_id>', methods=['POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 deleta seus pr\u00f3prios itens
@own_expense_revenue_required
def delete_despesa_receita(item_id):
    """
    Deleta um item de despesa/receita. Apenas via POST para seguran\u00e7a.
    """
    if DespesaReceita.delete(item_id, current_user.id):
        flash('Item de despesa/receita deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar item de despesa/receita.', 'danger')
    return redirect(url_for('despesa_receita.list_despesas_receitas'))
