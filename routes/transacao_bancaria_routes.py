# routes/transacao_bancaria_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.transacao_bancaria_model import TransacaoBancaria
from functools import wraps

bp_transacao_bancaria = Blueprint(
    'transacao_bancaria', __name__, url_prefix='/transacoes')

TIPOS_TRANSACAO = ["Crédito", "Débito"]


def own_transaction_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    sua própria transação bancária.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        transacao_id = kwargs.get('transacao_id')
        if transacao_id:
            transacao = TransacaoBancaria.get_by_id(
                transacao_id, current_user.id)
            if not transacao:
                flash(
                    'Transação bancária não encontrada ou você não tem permissão para acessá-la.', 'danger')
                return redirect(url_for('transacao_bancaria.list_transacoes'))
        return f(*args, **kwargs)
    return decorated_function


@bp_transacao_bancaria.route('/')
@login_required
def list_transacoes():
    """
    Lista todas as transações bancárias do usuário logado.
    """
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)
    return render_template('transacao_bancaria/list.html', transacoes=transacoes)


@bp_transacao_bancaria.route('/add', methods=['GET', 'POST'])
@login_required
def add_transacao():
    """
    Adiciona uma nova transação bancária para o usuário logado.
    """
    if request.method == 'POST':
        transacao_desc = request.form.get('transacao')
        tipo = request.form.get('tipo')

        try:
            if not transacao_desc:
                flash('O campo "Transação" não pode ser vazio.', 'danger')
                return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)
            if tipo not in TIPOS_TRANSACAO:
                flash('Tipo de transação inválido.', 'danger')
                return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)

            TransacaoBancaria.add(
                user_id=current_user.id,
                transacao=transacao_desc,
                tipo=tipo
            )
            flash('Transação bancária adicionada com sucesso!', 'success')
            return redirect(url_for('transacao_bancaria.list_transacoes'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar a transação bancária: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar transação bancária: {e}", exc_info=True)

    return render_template('transacao_bancaria/add.html', TIPOS_TRANSACAO=TIPOS_TRANSACAO)


@bp_transacao_bancaria.route('/edit/<int:transacao_id>', methods=['GET', 'POST'])
@login_required
@own_transaction_required
def edit_transacao(transacao_id):
    """
    Edita uma transação bancária existente.
    """
    transacao = TransacaoBancaria.get_by_id(transacao_id, current_user.id)
    if not transacao:
        flash('Transação bancária não encontrada.', 'danger')
        return redirect(url_for('transacao_bancaria.list_transacoes'))

    if request.method == 'POST':
        transacao_desc = request.form.get('transacao')
        tipo = request.form.get('tipo')

        try:
            if not transacao_desc:
                flash('O campo "Transação" não pode ser vazio.', 'danger')
                return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)
            if tipo not in TIPOS_TRANSACAO:
                flash('Tipo de transação inválido.', 'danger')
                return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)

            updated_transacao = TransacaoBancaria.update(
                transacao_id=transacao_id,
                user_id=current_user.id,
                transacao=transacao_desc,
                tipo=tipo
            )
            if updated_transacao:
                flash(
                    'Transação bancária atualizada com sucesso!', 'success')
                return redirect(url_for('transacao_bancaria.list_transacoes'))
            else:
                flash('Erro ao atualizar transação bancária.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar a transação bancária: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar transação bancária ID {transacao_id}: {e}", exc_info=True)

    return render_template('transacao_bancaria/edit.html', transacao=transacao, TIPOS_TRANSACAO=TIPOS_TRANSACAO)


@bp_transacao_bancaria.route('/delete/<int:transacao_id>', methods=['POST'])
@login_required
@own_transaction_required
def delete_transacao(transacao_id):
    """
    Deleta uma transação bancária. Apenas via POST para segurança.
    """
    if TransacaoBancaria.delete(transacao_id, current_user.id):
        flash('Transação bancária deletada com sucesso!', 'success')
    else:
        flash('Erro ao deletar transação bancária.', 'danger')
    return redirect(url_for('transacao_bancaria.list_transacoes'))
