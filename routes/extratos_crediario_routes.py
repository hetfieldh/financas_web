# routes/extratos_crediario_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.crediario_model import Crediario
from models.movimento_crediario_model import MovimentoCrediario
# Importar para obter o nome do grupo
from models.grupo_crediario_model import GrupoCrediario
from datetime import datetime, timedelta, date
from decimal import Decimal

# Define o Blueprint para as rotas de extratos de crediário
bp_extratos_crediario = Blueprint(
    'extratos_crediario', __name__, url_prefix='/extratos_crediario')


@bp_extratos_crediario.route('/crediario_form', methods=['GET', 'POST'])
@login_required
def crediario_form():
    """
    Exibe o formulário para seleção de crediário e mês/ano para o extrato.
    """
    # Busca todos os crediários associados ao usuário logado
    crediarios = Crediario.get_all_by_user(current_user.id)

    # Gera a lista de meses e anos para o filtro (últimos 12 meses, incluindo o atual)
    meses_anos = []
    today = datetime.now()
    for i in range(12):  # Gera os últimos 12 meses
        # Aproximação para ir para o mês anterior
        target_date = today - timedelta(days=30 * i)
        meses_anos.append({
            'value': target_date.strftime('%Y-%m'),
            'label': target_date.strftime('%m/%Y')
        })

    # Remove duplicatas e ordena a lista de meses/anos
    seen = set()
    unique_meses_anos = []
    for item in meses_anos:
        if item['value'] not in seen:
            unique_meses_anos.append(item)
            seen.add(item['value'])
    unique_meses_anos.sort(key=lambda x: datetime.strptime(
        x['value'], '%Y-%m'), reverse=True)

    # Lógica para processar a submissão do formulário (POST)
    if request.method == 'POST':
        crediario_id = request.form.get('crediario_id', type=int)
        mes_ano_selecionado = request.form.get('mes_ano')

        # Valida se os campos foram selecionados
        if not crediario_id or not mes_ano_selecionado:
            flash('Por favor, selecione um Crediário e um Mês/Ano.', 'danger')
            return redirect(url_for('extratos_crediario.crediario_form'))

        # Verifica se o crediário selecionado pertence ao usuário logado
        crediario_selecionado = Crediario.get_by_id(
            crediario_id, current_user.id)
        if not crediario_selecionado:
            flash('Crediário inválido ou não pertence a você.', 'danger')
            return redirect(url_for('extratos_crediario.crediario_form'))

        # Redireciona para a rota de visualização do extrato com os parâmetros selecionados
        return redirect(url_for('extratos_crediario.crediario_view',
                                crediario_id=crediario_id,
                                mes_ano=mes_ano_selecionado))

    # Renderiza o formulário para seleção (GET)
    return render_template('extratos/crediario_form.html',
                           crediarios=crediarios,
                           meses_anos=unique_meses_anos)


@bp_extratos_crediario.route('/crediario_view/<int:crediario_id>/<string:mes_ano>', methods=['GET'])
@login_required
def crediario_view(crediario_id, mes_ano):
    """
    Exibe o extrato de crediário para o crediário e mês/ano selecionados.
    """
    # Busca o objeto Crediario pelo ID e ID do usuário
    crediario = Crediario.get_by_id(crediario_id, current_user.id)
    if not crediario:
        flash(
            'Crediário não encontrado ou você não tem permissão para acessá-lo.', 'danger')
        return redirect(url_for('extratos_crediario.crediario_form'))

    try:
        # Converte a string mes_ano para um objeto datetime
        data_extrato_dt = datetime.strptime(mes_ano, '%Y-%m')
        mes_ano_formatado = data_extrato_dt.strftime('%m/%Y')
    except ValueError:
        flash('Formato de mês/ano inválido.', 'danger')
        return redirect(url_for('extratos_crediario.crediario_form'))

    # Obtém os movimentos de crediário para o crediário e mês/ano selecionados
    # A lógica no MovimentoCrediario.get_by_crediario_and_month filtra os movimentos
    # que têm parcelas ativas no mês/ano.
    movimentos_raw = MovimentoCrediario.get_by_crediario_and_month(
        current_user.id, crediario.id, data_extrato_dt.year, data_extrato_dt.month
    )

    # Processa os movimentos para incluir os nomes do crediário e grupo de crediário
    movimentos = []
    for mov in movimentos_raw:
        # Busca o nome do crediário
        crediario_obj = Crediario.get_by_id(mov.crediario_id, current_user.id)
        # Busca o nome do grupo de crediário
        grupo_crediario_obj = GrupoCrediario.get_by_id(
            mov.grupo_crediario_id, current_user.id)

        # Cria um dicionário para facilitar a passagem para o template
        mov_data = {
            'id': mov.id,
            'crediario': crediario_obj.crediario if crediario_obj else 'Desconhecido',
            'grupo_crediario': grupo_crediario_obj.grupo if grupo_crediario_obj else 'Desconhecido',
            'descricao': mov.descricao,
            'data_compra': mov.data_compra,
            'valor_total': mov.valor_total,
            'num_parcelas': mov.num_parcelas,
            'primeira_parcela': mov.primeira_parcela,
            'ultima_parcela': mov.ultima_parcela,
            'valor_parcela_mensal': mov.valor_parcela_mensal
        }
        movimentos.append(mov_data)

    # Renderiza o template de visualização do extrato
    return render_template('extratos/crediario_view.html',
                           crediario=crediario,
                           mes_ano_formatado=mes_ano_formatado,
                           movimentos=movimentos)
