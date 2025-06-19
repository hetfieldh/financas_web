# routes/movimento_bancario_routes.py

import json
import base64
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.movimento_bancario_model import MovimentoBancario
from models.conta_bancaria_model import ContaBancaria
from models.transacao_bancaria_model import TransacaoBancaria
from functools import wraps
from datetime import datetime, date
from decimal import Decimal

bp_movimento_bancario = Blueprint(
    'movimento_bancario', __name__, url_prefix='/movimentos')

TIPOS_MOVIMENTO = ["Despesa", "Receita"]


def own_movement_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_id = kwargs.get('movimento_id')
        if movimento_id:
            movimento = MovimentoBancario.get_by_id(
                movimento_id, current_user.id)
            if not movimento:
                flash(
                    'Movimento bancário não encontrado ou não tem permissão para aceder a ele.', 'danger')
                return redirect(url_for('movimento_bancario.list_movimentos'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_bancario.route('/')
@login_required
def list_movimentos():
    movimentos = MovimentoBancario.get_all_by_user(current_user.id)
    for mov in movimentos:
        mov.conta_detalhes = ContaBancaria.get_by_id(
            mov.conta_bancaria_id, current_user.id)
        mov.transacao_detalhes = TransacaoBancaria.get_by_id(
            mov.transacao_bancaria_id, current_user.id)
        mov.data_formatada = mov.data.strftime('%d/%m/%Y') if mov.data else ''

    return render_template('movimento_bancario/list.html', movimentos=movimentos)


@bp_movimento_bancario.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento():
    contas = ContaBancaria.get_all_by_user(current_user.id)
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)

    transacoes_json_data = [
        {'id': t.id, 'transacao': t.transacao, 'tipo': t.tipo} for t in transacoes]
    transacoes_json_string = json.dumps(transacoes_json_data)
    transacoes_base64_string = base64.b64encode(
        transacoes_json_string.encode('utf-8')).decode('utf-8')

    today_date = date.today().isoformat()

    if not contas:
        flash('Precisa de registar pelo menos uma conta bancária antes de adicionar um movimento.', 'warning')
        return redirect(url_for('conta_bancaria.add_conta'))
    if not transacoes:
        flash('Precisa de registar pelo menos um tipo de transação bancária (Crédito/Débito) antes de adicionar um movimento.', 'warning')
        return redirect(url_for('transacao_bancaria.add_transacao'))

    if request.method == 'POST':
        conta_bancaria_id = request.form.get('conta_bancaria_id', type=int)
        transacao_bancaria_id = request.form.get(
            'transacao_bancaria_id', type=int)
        data_str = request.form.get('data')
        valor_str = request.form.get('valor')
        tipo = request.form.get('tipo_hidden')

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
            valor = Decimal(valor_str)

            selected_transacao = TransacaoBancaria.get_by_id(
                transacao_bancaria_id, current_user.id)
            if not selected_transacao:
                flash(
                    'Transação selecionada não encontrada ou não lhe pertence.', 'danger')
                return render_template('movimento_bancario/add.html',
                                       contas=contas, transacoes=transacoes,
                                       TIPOS_MOVIMENTO=TIPOS_MOVIMENTO, today_date=today_date,
                                       transacoes_json_data=transacoes_base64_string)

            if (selected_transacao.tipo == 'Crédito' and valor < 0) or \
               (selected_transacao.tipo == 'Débito' and valor > 0):
                flash(
                    f'O valor introduzido ({valor_str}) é inválido para o tipo de transação "{selected_transacao.tipo}".', 'danger')
                return render_template('movimento_bancario/add.html',
                                       contas=contas, transacoes=transacoes,
                                       TIPOS_MOVIMENTO=TIPOS_MOVIMENTO, today_date=today_date,
                                       transacoes_json_data=transacoes_base64_string)

            MovimentoBancario.add(
                user_id=current_user.id,
                conta_bancaria_id=conta_bancaria_id,
                transacao_bancaria_id=transacao_bancaria_id,
                data=data,
                valor=valor,
                tipo=tipo
            )

            flash('Movimento bancário adicionado com sucesso!', 'success')
            return redirect(url_for('movimento_bancario.list_movimentos'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o movimento bancário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar movimento bancário: {e}", exc_info=True)

    return render_template('movimento_bancario/add.html',
                           contas=contas, transacoes=transacoes,
                           TIPOS_MOVIMENTO=TIPOS_MOVIMENTO, today_date=today_date,
                           transacoes_json_data=transacoes_base64_string)


@bp_movimento_bancario.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
@own_movement_required
def edit_movimento(movimento_id):
    movimento = MovimentoBancario.get_by_id(movimento_id, current_user.id)
    if not movimento:
        flash('Movimento bancário não encontrado.', 'danger')
        return redirect(url_for('movimento_bancario.list_movimentos'))

    contas = ContaBancaria.get_all_by_user(current_user.id)
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)

    transacoes_json_data = [
        {'id': t.id, 'transacao': t.transacao, 'tipo': t.tipo} for t in transacoes]
    transacoes_json_string = json.dumps(transacoes_json_data)
    transacoes_base64_string = base64.b64encode(
        transacoes_json_string.encode('utf-8')).decode('utf-8')

    movimento_date_str = movimento.data.strftime(
        '%Y-%m-%d') if isinstance(movimento.data, (datetime, date)) else ''

    if not contas:
        flash('Precisa de registar pelo menos uma conta bancária.', 'warning')
        return redirect(url_for('conta_bancaria.add_conta'))
    if not transacoes:
        flash(
            'Precisa de registar pelo menos um tipo de transação bancária.', 'warning')
        return redirect(url_for('transacao_bancaria.add_transacao'))

    if request.method == 'POST':
        nova_conta_bancaria_id = request.form.get(
            'conta_bancaria_id', type=int)
        nova_transacao_bancaria_id = request.form.get(
            'transacao_bancaria_id', type=int)
        nova_data_str = request.form.get('data')
        novo_valor_str = request.form.get('valor')
        novo_tipo = request.form.get('tipo_hidden')

        old_valor = movimento.valor
        old_tipo = movimento.tipo

        try:
            nova_data = datetime.strptime(nova_data_str, '%Y-%m-%d').date()
            novo_valor = Decimal(novo_valor_str)

            selected_transacao = TransacaoBancaria.get_by_id(
                nova_transacao_bancaria_id, current_user.id)
            if not selected_transacao:
                flash(
                    'Transação selecionada não encontrada ou não lhe pertence.', 'danger')
                return render_template('movimento_bancario/edit.html',
                                       movimento=movimento, contas=contas,
                                       transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                                       movimento_date_str=movimento_date_str,
                                       transacoes_json_data=transacoes_base64_string)

            if (selected_transacao.tipo == 'Crédito' and novo_valor < 0) or \
               (selected_transacao.tipo == 'Débito' and novo_valor > 0):
                flash(
                    f'O valor introduzido ({novo_valor_str}) é inválido para o tipo de transação "{selected_transacao.tipo}".', 'danger')
                return render_template('movimento_bancario/edit.html',
                                       movimento=movimento, contas=contas,
                                       transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                                       movimento_date_str=movimento_date_str,
                                       transacoes_json_data=transacoes_base64_string)

            updated_movimento = MovimentoBancario.update(
                movimento_id=movimento_id,
                user_id=current_user.id,
                conta_bancaria_id=nova_conta_bancaria_id,
                transacao_bancaria_id=nova_transacao_bancaria_id,
                data=nova_data,
                valor=novo_valor,
                tipo=novo_tipo,
                old_valor=old_valor,
                old_tipo=old_tipo
            )
            if updated_movimento:
                flash('Movimento bancário atualizado com sucesso!', 'success')
                return redirect(url_for('movimento_bancario.list_movimentos'))
            else:
                flash('Erro ao atualizar movimento bancário.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o movimento bancário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar movimento bancário ID {movimento_id}: {e}", exc_info=True)

    return render_template('movimento_bancario/edit.html',
                           movimento=movimento, contas=contas,
                           transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                           movimento_date_str=movimento_date_str,
                           transacoes_json_data=transacoes_base64_string)


@bp_movimento_bancario.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
@own_movement_required
def delete_movimento(movimento_id):
    movimento_a_deletar = MovimentoBancario.get_by_id(
        movimento_id, current_user.id)
    if not movimento_a_deletar:
        flash('Movimento bancário não encontrado para deleção.', 'danger')
        return redirect(url_for('movimento_bancario.list_movimentos'))

    try:
        # AQUI FOI FEITA A MUDANÇA: Agora, apenas os argumentos esperados são passados.
        if MovimentoBancario.delete(movimento_id, current_user.id):
            flash('Movimento bancário deletado com sucesso!', 'success')
        else:
            flash('Erro ao deletar movimento bancário.', 'danger')
    except ValueError as e:
        flash(f'Erro ao deletar movimento: {e}', 'danger')
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao tentar deletar o movimento bancário: {e}', 'danger')
        current_app.logger.error(
            f"Erro ao deletar movimento bancário ID {movimento_id}: {e}", exc_info=True)
    return redirect(url_for('movimento_bancario.list_movimentos'))