# routes/despesa_fixa_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.despesa_fixa_model import DespesaFixa
from models.despesa_receita_model import DespesaReceita
from functools import wraps
from decimal import Decimal
from datetime import date, datetime

bp_despesa_fixa = Blueprint(
    'despesa_fixa', __name__, url_prefix='/despesas_fixas')


def own_fixed_expense_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio item de despesa fixa.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        despesa_fixa_id = kwargs.get('despesa_fixa_id')
        if despesa_fixa_id:
            despesa = DespesaFixa.get_by_id(despesa_fixa_id, current_user.id)
            if not despesa:
                flash(
                    'Despesa fixa não encontrada ou você não tem permissão para acessá-la.', 'danger')
                return redirect(url_for('despesa_fixa.list_despesas_fixas'))
        return f(*args, **kwargs)
    return decorated_function


@bp_despesa_fixa.route('/')
@login_required
def list_despesas_fixas():
    """
    Lista todos os itens de despesa fixa do usuário logado.
    Para exibir detalhes da despesa/receita, buscamos os objetos completos.
    """
    despesas_fixas = DespesaFixa.get_all_by_user(current_user.id)
    for despesa_fixa in despesas_fixas:
        despesa_fixa.despesa_receita_detalhes = DespesaReceita.get_by_id(
            despesa_fixa.despesa_receita_id, current_user.id)
        despesa_fixa.mes_ano_formatado = despesa_fixa.mes_ano.strftime(
            '%m/%Y') if despesa_fixa.mes_ano else ''

    return render_template('despesa_fixa/list.html', despesas_fixas=despesas_fixas)


@bp_despesa_fixa.route('/add', methods=['GET', 'POST'])
@login_required
def add_despesa_fixa():
    """
    Adiciona um novo item de despesa fixa para o usuário logado.
    """
    despesas_receitas_disponiveis = DespesaReceita.get_all_by_user(
        current_user.id)

    if not despesas_receitas_disponiveis:
        flash('Precisa de registar pelo menos um tipo de Despesa/Receita antes de adicionar uma despesa fixa.', 'warning')
        return redirect(url_for('despesa_receita.add_despesa_receita'))

    current_month_year = date.today().strftime('%Y-%m')

    if request.method == 'POST':
        despesa_receita_id = request.form.get('despesa_receita_id', type=int)
        mes_ano_str = request.form.get('mes_ano')
        valor_str = request.form.get('valor').replace(',', '.')

        try:
            valor = Decimal(valor_str)
            if valor <= 0:
                raise ValueError("O valor deve ser maior que zero.")

            if not DespesaReceita.get_by_id(despesa_receita_id, current_user.id):
                raise ValueError(
                    "Tipo de Despesa/Receita inválido ou não pertence a você.")

            DespesaFixa.add(
                user_id=current_user.id,
                despesa_receita_id=despesa_receita_id,
                mes_ano_str=mes_ano_str,
                valor=valor
            )

            flash('Despesa fixa adicionada com sucesso!', 'success')
            return redirect(url_for('despesa_fixa.list_despesas_fixas'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar a despesa fixa: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar despesa fixa: {e}", exc_info=True)

    return render_template('despesa_fixa/add.html',
                           despesas_receitas=despesas_receitas_disponiveis,
                           current_month_year=current_month_year)


@bp_despesa_fixa.route('/edit/<int:despesa_fixa_id>', methods=['GET', 'POST'])
@login_required
@own_fixed_expense_required
def edit_despesa_fixa(despesa_fixa_id):
    """
    Edita um item de despesa fixa existente.
    """
    despesa_fixa = DespesaFixa.get_by_id(despesa_fixa_id, current_user.id)
    if not despesa_fixa:
        flash('Despesa fixa não encontrada.', 'danger')
        return redirect(url_for('despesa_fixa.list_despesas_fixas'))

    despesas_receitas_disponiveis = DespesaReceita.get_all_by_user(
        current_user.id)

    mes_ano_str = despesa_fixa.mes_ano.strftime(
        '%Y-%m') if despesa_fixa.mes_ano else ''

    if not despesas_receitas_disponiveis:
        flash('Precisa de registar pelo menos um tipo de Despesa/Receita.', 'warning')
        return redirect(url_for('despesa_receita.add_despesa_receita'))

    if request.method == 'POST':
        despesa_receita_id = request.form.get('despesa_receita_id', type=int)
        mes_ano_str_form = request.form.get('mes_ano')
        valor_str = request.form.get('valor').replace(',', '.')

        try:
            valor = Decimal(valor_str)
            if valor <= 0:
                raise ValueError("O valor deve ser maior que zero.")

            if not DespesaReceita.get_by_id(despesa_receita_id, current_user.id):
                raise ValueError(
                    "Tipo de Despesa/Receita inválido ou não pertence a você.")

            updated_despesa_fixa = DespesaFixa.update(
                despesa_fixa_id=despesa_fixa_id,
                user_id=current_user.id,
                despesa_receita_id=despesa_receita_id,
                mes_ano_str=mes_ano_str_form,
                valor=valor
            )
            if updated_despesa_fixa:
                flash('Despesa fixa atualizada com sucesso!', 'success')
                return redirect(url_for('despesa_fixa.list_despesas_fixas'))
            else:
                flash('Erro ao atualizar despesa fixa.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar a despesa fixa: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar despesa fixa ID {despesa_fixa_id}: {e}", exc_info=True)

    return render_template('despesa_fixa/edit.html',
                           despesa_fixa=despesa_fixa,
                           despesas_receitas=despesas_receitas_disponiveis,
                           mes_ano_str=mes_ano_str)


@bp_despesa_fixa.route('/delete/<int:despesa_fixa_id>', methods=['POST'])
@login_required
@own_fixed_expense_required
def delete_despesa_fixa(despesa_fixa_id):
    """
    Deleta um item de despesa fixa. Apenas via POST para segurança.
    """
    if DespesaFixa.delete(despesa_fixa_id, current_user.id):
        flash('Despesa fixa deletada com sucesso!', 'success')
    else:
        flash('Erro ao deletar despesa fixa.', 'danger')
    return redirect(url_for('despesa_fixa.list_despesas_fixas'))
