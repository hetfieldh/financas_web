# routes/movimento_renda_routes.py

import json
import base64
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.movimento_renda_model import MovimentoRenda
from models.renda_model import Renda
from functools import wraps
from datetime import datetime, date
from decimal import Decimal

bp_movimento_renda = Blueprint(
    'movimento_renda', __name__, url_prefix='/movimentos_renda')


def own_movement_renda_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio movimento de renda.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_id = kwargs.get('movimento_id')
        if movimento_id:
            movimento = MovimentoRenda.get_by_id(
                movimento_id, current_user.id)
            if not movimento:
                flash(
                    'Movimento de renda não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('movimento_renda.list_movimentos_renda'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_renda.route('/')
@login_required
def list_movimentos_renda():
    """
    Lista todos os movimentos de renda do usuário logado.
    """
    movimentos = MovimentoRenda.get_all_by_user(current_user.id)
    return render_template('movimento_renda/list.html', movimentos=movimentos)


@bp_movimento_renda.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento_renda():
    """
    Adiciona um novo movimento de renda para o usuário logado.
    """
    rendas = Renda.get_all_by_user(
        current_user.id)

    today_month_year = date.today().strftime('%Y-%m')

    if not rendas:
        flash('Você precisa registrar pelo menos uma Renda antes de adicionar um movimento.', 'warning')
        return redirect(url_for('renda.add_renda'))

    if request.method == 'POST':
        renda_id = request.form.get('renda_id', type=int)
        mes_ref_str = request.form.get('mes_ref')
        mes_pagto_str = request.form.get('mes_pagto')
        valor_str = request.form.get('valor')

        try:
            mes_ref = datetime.strptime(mes_ref_str, '%Y-%m').date()
            mes_pagto = datetime.strptime(mes_pagto_str, '%Y-%m').date()

            valor = Decimal(valor_str.replace(',', '.'))

            if not renda_id or not mes_ref or not mes_pagto or valor is None:
                raise ValueError(
                    "Todos os campos obrigatórios devem ser preenchidos.")

            MovimentoRenda.add(
                user_id=current_user.id,
                renda_id=renda_id,
                mes_ref=mes_ref,
                mes_pagto=mes_pagto,
                valor=valor
            )

            flash('Movimento de renda adicionado com sucesso!', 'success')
            return redirect(url_for('movimento_renda.list_movimentos_renda'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o movimento de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar movimento de renda (UserID: {current_user.id}): {e}", exc_info=True)

    return render_template('movimento_renda/add.html',
                           rendas=rendas,
                           today_month_year=today_month_year)


@bp_movimento_renda.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
@own_movement_renda_required
def edit_movimento_renda(movimento_id):
    """
    Edita um movimento de renda existente.
    """
    movimento = MovimentoRenda.get_by_id(movimento_id, current_user.id)
    if not movimento:
        flash('Movimento de renda não encontrado.', 'danger')
        return redirect(url_for('movimento_renda.list_movimentos_renda'))

    rendas = Renda.get_all_by_user(current_user.id)

    mes_ref_month_year = movimento.mes_ref.strftime(
        '%Y-%m') if isinstance(movimento.mes_ref, (datetime, date)) else ''
    mes_pagto_month_year = movimento.mes_pagto.strftime(
        '%Y-%m') if isinstance(movimento.mes_pagto, (datetime, date)) else ''

    if not rendas:
        flash('Você precisa registrar pelo menos uma Renda.', 'warning')
        return redirect(url_for('renda.add_renda'))

    if request.method == 'POST':
        renda_id = request.form.get('renda_id', type=int)
        mes_ref_str = request.form.get('mes_ref')
        mes_pagto_str = request.form.get('mes_pagto')
        valor_str = request.form.get('valor')

        try:
            mes_ref = datetime.strptime(mes_ref_str, '%Y-%m').date()
            mes_pagto = datetime.strptime(mes_pagto_str, '%Y-%m').date()
            valor = Decimal(valor_str.replace(',', '.'))

            if not renda_id or not mes_ref or not mes_pagto or valor is None:
                raise ValueError(
                    "Todos os campos obrigatórios devem ser preenchidos.")

            updated_movimento = MovimentoRenda.update(
                movimento_id=movimento_id,
                user_id=current_user.id,
                renda_id=renda_id,
                mes_ref=mes_ref,
                mes_pagto=mes_pagto,
                valor=valor
            )
            if updated_movimento:
                flash('Movimento de renda atualizado com sucesso!', 'success')
                return redirect(url_for('movimento_renda.list_movimentos_renda'))
            else:
                flash('Erro ao atualizar movimento de renda.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o movimento de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar movimento de renda ID {movimento_id} (UserID: {current_user.id}): {e}", exc_info=True)

    return render_template('movimento_renda/edit.html',
                           movimento=movimento,
                           rendas=rendas,
                           mes_ref_month_year=mes_ref_month_year,
                           mes_pagto_month_year=mes_pagto_month_year)


@bp_movimento_renda.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
@own_movement_renda_required
def delete_movimento_renda(movimento_id):
    """
    Deleta um movimento de renda. Apenas via POST para segurança.
    """
    try:
        if MovimentoRenda.delete(movimento_id, current_user.id):
            flash('Movimento de renda deletado com sucesso!', 'success')
        else:
            flash('Erro ao deletar movimento de renda.', 'danger')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')
        current_app.logger.warning(
            f"Erro de validação ao deletar movimento de renda ID {movimento_id} (UserID: {current_user.id}): {e}")
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao deletar o movimento de renda: {e}', 'danger')
        current_app.logger.error(
            f"Erro inesperado ao deletar movimento de renda ID {movimento_id} (UserID: {current_user.id}): {e}", exc_info=True)
    return redirect(url_for('movimento_renda.list_movimentos_renda'))
