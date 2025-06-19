# routes/movimento_renda_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.movimento_renda_model import MovimentoRenda
from models.renda_model import Renda
from functools import wraps
from decimal import Decimal
from datetime import date, datetime
import json
import base64

bp_movimento_renda = Blueprint(
    'movimentos_renda', __name__, url_prefix='/movimentos_renda')


def own_movimento_renda_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio item de movimento de renda.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_renda_id = kwargs.get('id')
        if movimento_renda_id:
            movimento = MovimentoRenda.get_by_id(
                movimento_renda_id, current_user.id)
            if not movimento:
                flash(
                    'Movimento de renda não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('movimentos_renda.list_movimentos_renda'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_renda.route('/')
@login_required
def list_movimentos_renda():
    """
    Lista todos os movimentos de renda do usuário logado.
    Busca os detalhes dos itens de renda associados para exibição.
    """
    movimentos_renda = MovimentoRenda.get_all_by_user(current_user.id)

    rendas_map = {r.id: r for r in Renda.get_all_by_user(current_user.id)}

    for movimento in movimentos_renda:
        movimento.renda_detalhes = rendas_map.get(movimento.renda_id)
        movimento.mes_ref_formatado = movimento.mes_ref.strftime(
            '%m/%Y') if movimento.mes_ref else ''
        movimento.mes_pagto_formatado = movimento.mes_pagto.strftime(
            '%m/%Y') if movimento.mes_pagto else ''

    return render_template('movimento_renda/list.html', movimentos_renda=movimentos_renda)


@bp_movimento_renda.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento_renda():
    """
    Adiciona um novo movimento de renda para o usuário logado.
    """
    rendas_disponiveis = Renda.get_all_by_user(current_user.id)

    if not rendas_disponiveis:
        flash('Você precisa registrar pelo menos um item de Renda (Provento, Desconto, etc.) antes de adicionar um movimento de renda.', 'warning')
        return redirect(url_for('renda.add_renda'))

    current_month_year = date.today().strftime('%Y-%m')

    rendas_serializaveis = [
        {'id': r.id, 'descricao': r.descricao, 'tipo': r.tipo} for r in rendas_disponiveis]
    rendas_json_data = base64.b64encode(json.dumps(
        rendas_serializaveis).encode('utf-8')).decode('utf-8')

    if request.method == 'POST':
        renda_id = request.form.get('renda_id', type=int)
        mes_ref_str = request.form.get('mes_ref')
        mes_pagto_str = request.form.get('mes_pagto')
        valor_str = request.form.get('valor')

        try:
            valor = Decimal(valor_str)

            renda_selecionada = Renda.get_by_id(renda_id, current_user.id)
            if not renda_selecionada:
                raise ValueError(
                    "Item de Renda inválido ou não pertence a você.")

            if valor == 0:
                raise ValueError("O valor não pode ser zero.")

            if renda_selecionada.tipo == 'Desconto':
                if valor > 0:
                    raise ValueError(
                        "Para Descontos, o valor deve ser negativo.")
            elif renda_selecionada.tipo in ['Provento', 'Benefício']:
                if valor < 0:
                    raise ValueError(
                        "Para Proventos ou Benefícios, o valor deve ser positivo.")

            MovimentoRenda.add(
                user_id=current_user.id,
                renda_id=renda_id,
                mes_ref_str=mes_ref_str,
                mes_pagto_str=mes_pagto_str,
                valor=valor
            )
            flash('Movimento de renda adicionado com sucesso!', 'success')
            return redirect(url_for('movimentos_renda.list_movimentos_renda'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
            return render_template('movimento_renda/add.html',
                                   rendas_disponiveis=rendas_disponiveis,
                                   current_month_year=current_month_year,
                                   form_data=request.form,
                                   rendas_json_data=rendas_json_data)
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o movimento de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar movimento de renda para user_id {current_user.id}: {e}", exc_info=True)
            return render_template('movimento_renda/add.html',
                                   rendas_disponiveis=rendas_disponiveis,
                                   current_month_year=current_month_year,
                                   form_data=request.form,
                                   rendas_json_data=rendas_json_data)

    return render_template('movimento_renda/add.html',
                           rendas_disponiveis=rendas_disponiveis,
                           current_month_year=current_month_year,
                           form_data={},
                           rendas_json_data=rendas_json_data)


@bp_movimento_renda.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@own_movimento_renda_required
def edit_movimento_renda(id):
    """
    Edita um item de movimento de renda existente.
    """
    movimento = MovimentoRenda.get_by_id(id, current_user.id)
    if not movimento:
        flash('Movimento de renda não encontrado.', 'danger')
        return redirect(url_for('movimentos_renda.list_movimentos_renda'))

    rendas_disponiveis = Renda.get_all_by_user(current_user.id)

    if not rendas_disponiveis:
        flash('Você precisa registrar pelo menos um item de Renda.', 'warning')
        return redirect(url_for('renda.add_renda'))

    mes_ref_str = movimento.mes_ref.strftime(
        '%Y-%m') if movimento.mes_ref else ''
    mes_pagto_str = movimento.mes_pagto.strftime(
        '%Y-%m') if movimento.mes_pagto else ''

    rendas_serializaveis = [
        {'id': r.id, 'descricao': r.descricao, 'tipo': r.tipo} for r in rendas_disponiveis]
    rendas_json_data = base64.b64encode(json.dumps(
        rendas_serializaveis).encode('utf-8')).decode('utf-8')

    if request.method == 'POST':
        renda_id = request.form.get('renda_id', type=int)
        mes_ref_str_form = request.form.get('mes_ref')
        mes_pagto_str_form = request.form.get('mes_pagto')
        valor_str = request.form.get('valor')

        try:
            valor = Decimal(valor_str)

            renda_selecionada = Renda.get_by_id(renda_id, current_user.id)
            if not renda_selecionada:
                raise ValueError(
                    "Item de Renda inválido ou não pertence a você.")

            if valor == 0:
                raise ValueError("O valor não pode ser zero.")

            if renda_selecionada.tipo == 'Desconto':
                if valor > 0:
                    raise ValueError(
                        "Para Descontos, o valor deve ser negativo.")
            elif renda_selecionada.tipo in ['Provento', 'Benefício']:
                if valor < 0:
                    raise ValueError(
                        "Para Proventos ou Benefícios, o valor deve ser positivo.")

            updated_movimento = MovimentoRenda.update(
                movimento_renda_id=id,
                user_id=current_user.id,
                renda_id=renda_id,
                mes_ref_str=mes_ref_str_form,
                mes_pagto_str=mes_pagto_str_form,
                valor=valor
            )
            if updated_movimento:
                flash('Movimento de renda atualizado com sucesso!', 'success')
                return redirect(url_for('movimentos_renda.list_movimentos_renda'))
            else:
                flash('Erro ao atualizar movimento de renda.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
            movimento.renda_id = renda_id
            movimento.mes_ref = datetime.strptime(
                mes_ref_str_form, '%Y-%m').date() if mes_ref_str_form else None
            movimento.mes_pagto = datetime.strptime(
                mes_pagto_str_form, '%Y-%m').date() if mes_pagto_str_form else None
            movimento.valor = valor
            mes_ref_str = mes_ref_str_form
            mes_pagto_str = mes_pagto_str_form
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o movimento de renda: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar movimento de renda ID {id}: {e}", exc_info=True)
            movimento.renda_id = renda_id
            movimento.mes_ref = datetime.strptime(
                mes_ref_str_form, '%Y-%m').date() if mes_ref_str_form else None
            movimento.mes_pagto = datetime.strptime(
                mes_pagto_str_form, '%Y-%m').date() if mes_pagto_str_form else None
            movimento.valor = valor
            mes_ref_str = mes_ref_str_form
            mes_pagto_str = mes_pagto_str_form

    return render_template('movimento_renda/edit.html',
                           movimento=movimento,
                           rendas_disponiveis=rendas_disponiveis,
                           mes_ref_str=mes_ref_str,
                           mes_pagto_str=mes_pagto_str,
                           rendas_json_data=rendas_json_data)


@bp_movimento_renda.route('/delete/<int:id>', methods=['POST'])
@login_required
@own_movimento_renda_required
def delete_movimento_renda(id):
    """
    Deleta um movimento de renda. Apenas via POST para segurança.
    """
    if MovimentoRenda.delete(id, current_user.id):
        flash('Movimento de renda deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar movimento de renda.', 'danger')
    return redirect(url_for('movimentos_renda.list_movimentos_renda'))
