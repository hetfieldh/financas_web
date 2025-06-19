# routes/extratos_bancarios_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.conta_bancaria_model import ContaBancaria
from models.movimento_bancario_model import MovimentoBancario
from models.transacao_bancaria_model import TransacaoBancaria
from datetime import datetime, date, timedelta
from decimal import Decimal

bp_extratos_bancario = Blueprint(
    'extratos_bancario', __name__, url_prefix='/extratos_bancario')


@bp_extratos_bancario.route('/bancario_form', methods=['GET', 'POST'])
@login_required
def bancario_form():
    contas = ContaBancaria.get_all_by_user(current_user.id)

    meses_anos = []
    today = datetime.now()
    for i in range(12):
        target_date = today - timedelta(days=30 * i)
        meses_anos.append({
            'value': target_date.strftime('%Y-%m'),
            'label': target_date.strftime('%m/%Y')
        })

    seen = set()
    unique_meses_anos = []
    for item in meses_anos:
        if item['value'] not in seen:
            unique_meses_anos.append(item)
            seen.add(item['value'])

    unique_meses_anos.sort(key=lambda x: datetime.strptime(
        x['value'], '%Y-%m'), reverse=True)

    if request.method == 'POST':
        conta_id = request.form.get('conta_id', type=int)
        mes_ano_selecionado = request.form.get('mes_ano')

        if not conta_id or not mes_ano_selecionado:
            flash(
                'Por favor, selecione uma Conta Bancária e um Mês/Ano.', 'danger')
            return redirect(url_for('extratos_bancario.bancario_form'))

        conta_selecionada = ContaBancaria.get_by_id(conta_id, current_user.id)
        if not conta_selecionada:
            flash(
                'Conta bancária inválida ou não pertence a você.', 'danger')
            return redirect(url_for('extratos_bancario.bancario_form'))

        return redirect(url_for('extratos_bancario.bancario_view', conta_id=conta_id, mes_ano=mes_ano_selecionado))

    return render_template('extratos/bancario_form.html', contas=contas, meses_anos=unique_meses_anos)


@bp_extratos_bancario.route('/bancario_view/<int:conta_id>/<string:mes_ano>', methods=['GET'])
@login_required
def bancario_view(conta_id, mes_ano):
    conta = ContaBancaria.get_by_id(conta_id, current_user.id)
    if not conta:
        flash('Conta bancária não encontrada ou você não tem permissão para acessá-la.', 'danger')
        return redirect(url_for('extratos_bancario.bancario_form'))

    try:
        data_extrato_dt = datetime.strptime(mes_ano, '%Y-%m')
        mes_ano_formatado = data_extrato_dt.strftime('%m/%Y')
    except ValueError:
        flash('Formato de mês/ano inválido.', 'danger')
        return redirect(url_for('extratos_bancario.bancario_form'))

    start_of_month = data_extrato_dt.date()
    if data_extrato_dt.month == 12:
        end_of_month_exclusive = date(data_extrato_dt.year + 1, 1, 1)
    else:
        end_of_month_exclusive = date(
            data_extrato_dt.year, data_extrato_dt.month + 1, 1)

    saldo_inicial_mes = MovimentoBancario.get_balance_up_to_date(
        current_user.id, conta.id, start_of_month
    )

    movimentos = MovimentoBancario.get_by_account_and_month(
        current_user.id, conta.id, data_extrato_dt.year, data_extrato_dt.month
    )

    for mov in movimentos:
        mov.transacao_detalhes = TransacaoBancaria.get_by_id(
            mov.transacao_bancaria_id, current_user.id)

    saldo_final_mes = saldo_inicial_mes
    for mov in movimentos:
        saldo_final_mes += mov.valor

    return render_template('extratos/bancario_view.html',
                           conta=conta,
                           mes_ano_formatado=mes_ano_formatado,
                           saldo_inicial=saldo_inicial_mes,
                           movimentos=movimentos,
                           saldo_final=saldo_final_mes)
