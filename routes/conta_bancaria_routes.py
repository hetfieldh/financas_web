# routes/conta_bancaria_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.conta_bancaria_model import ContaBancaria
from functools import wraps

bp_conta_bancaria = Blueprint('conta_bancaria', __name__, url_prefix='/contas')

TIPOS_CONTA = ["Corrente", "Poupança", "Digital",
               "Restituições", "Vendas", "Serviços", "Outros"]


def own_account_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    sua própria conta bancária.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conta_id = kwargs.get('conta_id')
        if conta_id:
            conta = ContaBancaria.get_by_id(conta_id, current_user.id)
            if not conta:
                flash(
                    'Conta bancária não encontrada ou você não tem permissão para acessá-la.', 'danger')
                return redirect(url_for('conta_bancaria.list_contas'))
        return f(*args, **kwargs)
    return decorated_function


@bp_conta_bancaria.route('/')
@login_required
def list_contas():
    """
    Lista todas as contas bancárias do usuário logado.
    """
    contas = ContaBancaria.get_all_by_user(current_user.id)
    return render_template('conta_bancaria/list.html', contas=contas)


@bp_conta_bancaria.route('/add', methods=['GET', 'POST'])
@login_required
def add_conta():
    """
    Adiciona uma nova conta bancária para o usuário logado.
    """
    if request.method == 'POST':
        banco = request.form.get('banco')
        agencia = request.form.get('agencia')
        conta = request.form.get('conta')
        tipo = request.form.get('tipo')
        saldo_inicial_str = request.form.get('saldo_inicial').replace(
            ',', '.')
        saldo_atual_str = request.form.get('saldo_atual').replace(
            ',', '.')
        limite_str = request.form.get('limite').replace(
            ',', '.')

        try:
            saldo_inicial = float(saldo_inicial_str)
            saldo_atual = float(saldo_atual_str)
            limite = float(limite_str)

            if len(agencia) > 4:
                flash('O número da agência deve ter no máximo 4 caracteres.', 'danger')
                return render_template('conta_bancaria/add.html', TIPOS_CONTA=TIPOS_CONTA)

            ContaBancaria.add(
                user_id=current_user.id,
                banco=banco,
                agencia=agencia,
                conta=conta,
                tipo=tipo,
                saldo_inicial=saldo_inicial,
                saldo_atual=saldo_atual,
                limite=limite
            )
            flash('Conta bancária adicionada com sucesso!', 'success')
            return redirect(url_for('conta_bancaria.list_contas'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar a conta bancária: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar conta bancária: {e}", exc_info=True)

    return render_template('conta_bancaria/add.html', TIPOS_CONTA=TIPOS_CONTA)


@bp_conta_bancaria.route('/edit/<int:conta_id>', methods=['GET', 'POST'])
@login_required
@own_account_required
def edit_conta(conta_id):
    """
    Edita uma conta bancária existente.
    """
    conta = ContaBancaria.get_by_id(conta_id, current_user.id)
    if not conta:
        flash('Conta bancária não encontrada.', 'danger')
        return redirect(url_for('conta_bancaria.list_contas'))

    if request.method == 'POST':
        banco = request.form.get('banco')
        agencia = request.form.get('agencia')
        conta_num = request.form.get('conta')
        tipo = request.form.get('tipo')
        saldo_inicial_str = request.form.get('saldo_inicial').replace(',', '.')
        saldo_atual_str = request.form.get('saldo_atual').replace(',', '.')
        limite_str = request.form.get('limite').replace(',', '.')

        try:
            saldo_inicial = float(saldo_inicial_str)
            saldo_atual = float(saldo_atual_str)
            limite = float(limite_str)

            if len(agencia) > 4:
                flash('O número da agência deve ter no máximo 4 caracteres.', 'danger')
                return render_template('conta_bancaria/edit.html', conta=conta, TIPOS_CONTA=TIPOS_CONTA)

            updated_conta = ContaBancaria.update(
                conta_id=conta_id,
                user_id=current_user.id,
                banco=banco,
                agencia=agencia,
                conta=conta_num,
                tipo=tipo,
                saldo_inicial=saldo_inicial,
                saldo_atual=saldo_atual,
                limite=limite
            )
            if updated_conta:
                flash('Conta bancária atualizada com sucesso!', 'success')
                return redirect(url_for('conta_bancaria.list_contas'))
            else:
                flash('Erro ao atualizar conta bancária.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar a conta bancária: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar conta bancária ID {conta_id}: {e}", exc_info=True)

    return render_template('conta_bancaria/edit.html', conta=conta, TIPOS_CONTA=TIPOS_CONTA)


@bp_conta_bancaria.route('/delete/<int:conta_id>', methods=['POST'])
@login_required
@own_account_required
def delete_conta(conta_id):
    """
    Deleta uma conta bancária. Apenas via POST para segurança.
    """
    if ContaBancaria.delete(conta_id, current_user.id):
        flash('Conta bancária deletada com sucesso!', 'success')
    else:
        flash('Erro ao deletar conta bancária.', 'danger')
    return redirect(url_for('conta_bancaria.list_contas'))
