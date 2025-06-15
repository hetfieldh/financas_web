from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.conta_bancaria_model import ContaBancaria
from models.movimento_bancario_model import MovimentoBancario
from models.transacao_bancaria_model import TransacaoBancaria
from datetime import datetime, date, timedelta
from decimal import Decimal

# Cria um Blueprint para organizar as rotas relacionadas a extratos
bp_extratos = Blueprint('extratos', __name__, url_prefix='/extratos')


@bp_extratos.route('/bancario_form', methods=['GET', 'POST'])
@login_required
def bancario_form():
    """
    Exibe o formul\u00e1rio para sele\u00e7\u00e3o de conta banc\u00e1ria e m\u00eas/ano para o extrato.
    """
    contas = ContaBancaria.get_all_by_user(current_user.id)

    # Gerar a lista dos \u00faltimos 12 meses (M\u00eas/Ano)
    meses_anos = []
    today = datetime.now()
    for i in range(12):  # \u00daltimos 12 meses, incluindo o atual
        # Calcula o m\u00eas e ano subtraindo 'i' meses
        # usando relativedelta para lidar com viradas de ano corretamente
        # Aproxima\u00e7\u00e3o para o m\u00eas
        target_date = today - timedelta(days=30 * i)
        meses_anos.append({
            # Formato para o backend (AAAA-MM)
            'value': target_date.strftime('%Y-%m'),
            # Formato para exibi\u00e7\u00e3o (MM/AAAA)
            'label': target_date.strftime('%m/%Y')
        })

    # Remover duplicatas e ordenar do mais recente para o mais antigo
    # Usa um set para manter a ordem de inser\u00e7\u00e3o e evitar duplicatas
    seen = set()
    unique_meses_anos = []
    for item in meses_anos:
        if item['value'] not in seen:
            unique_meses_anos.append(item)
            seen.add(item['value'])

    # Ordenar novamente para garantir a ordem correta, j\u00e1 que o set n\u00e3o garante ordem
    unique_meses_anos.sort(key=lambda x: datetime.strptime(
        x['value'], '%Y-%m'), reverse=True)

    if request.method == 'POST':
        conta_id = request.form.get('conta_id', type=int)
        mes_ano_selecionado = request.form.get('mes_ano')  # AAAA-MM

        if not conta_id or not mes_ano_selecionado:
            flash(
                'Por favor, selecione uma Conta Banc\u00e1ria e um M\u00eas/Ano.', 'danger')
            return redirect(url_for('extratos.bancario_form'))

        # Verifica se a conta pertence ao usu\u00e1rio
        conta_selecionada = ContaBancaria.get_by_id(conta_id, current_user.id)
        if not conta_selecionada:
            flash(
                'Conta banc\u00e1ria inv\u00e1lida ou n\u00e3o pertence a voc\u00ea.', 'danger')
            return redirect(url_for('extratos.bancario_form'))

        # Redireciona para a tela do extrato, passando os par\u00e2metros
        return redirect(url_for('extratos.bancario_view', conta_id=conta_id, mes_ano=mes_ano_selecionado))

    return render_template('extratos/bancario_form.html', contas=contas, meses_anos=unique_meses_anos)


@bp_extratos.route('/bancario_view/<int:conta_id>/<string:mes_ano>', methods=['GET'])
@login_required
def bancario_view(conta_id, mes_ano):
    """
    Exibe o extrato banc\u00e1rio para a conta e m\u00eas/ano selecionados.
    Calcula saldo inicial e final.
    """
    conta = ContaBancaria.get_by_id(conta_id, current_user.id)
    if not conta:
        flash('Conta banc\u00e1ria n\u00e3o encontrada ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-la.', 'danger')
        return redirect(url_for('extratos.bancario_form'))

    try:
        # Tenta converter o mes_ano de string 'AAAA-MM' para um objeto datetime
        data_extrato_dt = datetime.strptime(mes_ano, '%Y-%m')
        mes_ano_formatado = data_extrato_dt.strftime('%m/%Y')
    except ValueError:
        flash('Formato de m\u00eas/ano inv\u00e1lido.', 'danger')
        return redirect(url_for('extratos.bancario_form'))

    # Calcular o in\u00edcio e o fim do m\u00eas do extrato
    start_of_month = data_extrato_dt.date()
    # Calcular o in\u00edcio do pr\u00f3ximo m\u00eas para usar como limite exclusivo para o saldo final
    if data_extrato_dt.month == 12:
        end_of_month_exclusive = date(data_extrato_dt.year + 1, 1, 1)
    else:
        end_of_month_exclusive = date(
            data_extrato_dt.year, data_extrato_dt.month + 1, 1)

    # Saldo Inicial do M\u00eas: Saldo inicial da conta + todos os movimentos at\u00e9 o dia anterior ao m\u00eas selecionado
    saldo_inicial_mes = MovimentoBancario.get_balance_up_to_date(
        current_user.id, conta.id, start_of_month
    )

    # Movimentos do m\u00eas selecionado
    movimentos = MovimentoBancario.get_by_account_and_month(
        current_user.id, conta.id, data_extrato_dt.year, data_extrato_dt.month
    )

    # Preparar movimentos para exibi\u00e7\u00e3o (adicionar detalhes de transa\u00e7\u00e3o)
    for mov in movimentos:
        # CORRIGIDO: Acessa transacao_bancaria_id, n\u00e3o transacao_id
        mov.transacao_detalhes = TransacaoBancaria.get_by_id(
            mov.transacao_bancaria_id, current_user.id)
        # Isso j\u00e1 est\u00e1 no modelo de listagem, mas \u00e9 bom garantir aqui tamb\u00e9m para a tela de extrato.

    # Saldo Final do M\u00eas: Saldo inicial do m\u00eas + todos os movimentos do m\u00eas
    saldo_final_mes = saldo_inicial_mes
    for mov in movimentos:
        if mov.tipo == 'Receita':
            saldo_final_mes += mov.valor
        else:  # Despesa
            saldo_final_mes -= mov.valor

    return render_template('extratos/bancario_view.html',
                           conta=conta,
                           mes_ano_formatado=mes_ano_formatado,
                           saldo_inicial=saldo_inicial_mes,
                           movimentos=movimentos,
                           saldo_final=saldo_final_mes)
