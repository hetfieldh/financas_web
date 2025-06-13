from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.transacao_bancaria_model import TransacaoBancaria
from functools import wraps

# Cria um Blueprint para organizar as rotas relacionadas a transa\u00e7\u00f5es banc\u00e1rias
bp_transacao_bancaria = Blueprint(
    'transacao_bancaria', __name__, url_prefix='/transacoes')

# Defini\u00e7\u00f5es de tipos de transa\u00e7\u00e3o para o formul\u00e1rio
TIPOS_TRANSACAO = ["Cr\u00e9dito", "D\u00e9bito"]


def own_transaction_required(f):
    """
    Decorador personalizado para garantir que o usu\u00e1rio est\u00e1 acessando ou modificando
    sua pr\u00f3pria transa\u00e7\u00e3o banc\u00e1ria.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        transacao_id = kwargs.get('transacao_id')
        if transacao_id:
            transacao = TransacaoBancaria.get_by_id(
                transacao_id, current_user.id)
            if not transacao:
                flash('Transa\u00e7\u00e3o banc\u00e1ria n\u00e3o encontrada ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-la.', 'danger')
                return redirect(url_for('transacao_bancaria.list_transacoes'))
        return f(*args, **kwargs)
    return decorated_function


@bp_transacao_bancaria.route('/')
@login_required
def list_transacoes():
    """
    Lista todas as transa\u00e7\u00f5es banc\u00e1rias do usu\u00e1rio logado.
    """
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)
    return render_template('transacao_bancaria/list.html', transacoes=transacoes)


@bp_transacao_bancaria.route('/add', methods=['GET', 'POST'])
@login_required
def add_transacao():
    """
    Adiciona uma nova transa\u00e7\u00e3o banc\u00e1ria para o usu\u00e1rio logado.
    """
    if request.method == 'POST':
        # Renomeado para evitar conflito com 'transacao' objeto
        transacao_desc = request.form.get('transacao')
        tipo = request.form.get('tipo')

        try:
            # Valida\u00e7\u00f5es adicionais
            if not transacao_desc:
                flash('O campo "Transa\u00e7\u00e3o" n\u00e3o pode ser vazio.', 'danger')
                return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)
            if tipo not in TIPOS_TRANSACAO:
                flash('Tipo de transa\u00e7\u00e3o inv\u00e1lido.', 'danger')
                return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)

            TransacaoBancaria.add(
                user_id=current_user.id,
                transacao=transacao_desc,
                tipo=tipo
            )
            flash('Transa\u00e7\u00e3o banc\u00e1ria adicionada com sucesso!', 'success')
            return redirect(url_for('transacao_bancaria.list_transacoes'))
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar a transa\u00e7\u00e3o banc\u00e1ria: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar transa\u00e7\u00e3o banc\u00e1ria: {e}", exc_info=True)

    return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)


@bp_transacao_bancaria.route('/edit/<int:transacao_id>', methods=['GET', 'POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 edita suas pr\u00f3prias transa\u00e7\u00f5es
@own_transaction_required
def edit_transacao(transacao_id):
    """
    Edita uma transa\u00e7\u00e3o banc\u00e1ria existente.
    """
    transacao = TransacaoBancaria.get_by_id(transacao_id, current_user.id)
    if not transacao:
        flash('Transa\u00e7\u00e3o banc\u00e1ria n\u00e3o encontrada.', 'danger')
        return redirect(url_for('transacao_bancaria.list_transacoes'))

    if request.method == 'POST':
        transacao_desc = request.form.get('transacao')
        tipo = request.form.get('tipo')

        try:
            if not transacao_desc:
                flash('O campo "Transa\u00e7\u00e3o" n\u00e3o pode ser vazio.', 'danger')
                return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)
            if tipo not in TIPOS_TRANSACAO:
                flash('Tipo de transa\u00e7\u00e3o inv\u00e1lido.', 'danger')
                return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)

            updated_transacao = TransacaoBancaria.update(
                transacao_id=transacao_id,
                user_id=current_user.id,
                transacao=transacao_desc,
                tipo=tipo
            )
            if updated_transacao:
                flash(
                    'Transa\u00e7\u00e3o banc\u00e1ria atualizada com sucesso!', 'success')
                return redirect(url_for('transacao_bancaria.list_transacoes'))
            else:
                flash('Erro ao atualizar transa\u00e7\u00e3o banc\u00e1ria.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar a transa\u00e7\u00e3o banc\u00e1ria: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar transa\u00e7\u00e3o banc\u00e1ria ID {transacao_id}: {e}", exc_info=True)

    return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)


@bp_transacao_bancaria.route('/delete/<int:transacao_id>', methods=['POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 deleta suas pr\u00f3prias transa\u00e7\u00f5es
@own_transaction_required
def delete_transacao(transacao_id):
    """
    Deleta uma transa\u00e7\u00e3o banc\u00e1ria. Apenas via POST para seguran\u00e7a.
    """
    if TransacaoBancaria.delete(transacao_id, current_user.id):
        flash('Transa\u00e7\u00e3o banc\u00e1ria deletada com sucesso!', 'success')
    else:
        flash('Erro ao deletar transa\u00e7\u00e3o banc\u00e1ria.', 'danger')
    return redirect(url_for('transacao_bancaria.list_transacoes'))
