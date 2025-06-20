# routes/movimento_crediario_routes.py

import json
import base64
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.movimento_crediario_model import MovimentoCrediario
from models.crediario_model import Crediario
from models.grupo_crediario_model import GrupoCrediario
from functools import wraps
from datetime import datetime, date
from decimal import Decimal

bp_movimento_crediario = Blueprint(
    'movimento_crediario', __name__, url_prefix='/movimentos_crediario')


def own_movement_crediario_required(f):
    """
    Decorador personalizado para garantir que o usuário está acessando ou modificando
    seu próprio movimento de crediário.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_id = kwargs.get('movimento_id')
        if movimento_id:
            movimento = MovimentoCrediario.get_by_id(
                movimento_id, current_user.id)
            if not movimento:
                flash(
                    'Movimento de crediário não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_crediario.route('/')
@login_required
def list_movimentos_crediario():
    """
    Lista todos os movimentos de crediário do usuário logado.
    Para exibir detalhes do grupo e crediário, buscamos os objetos completos.
    """
    movimentos = MovimentoCrediario.get_all_by_user(current_user.id)
    for mov in movimentos:
        mov.grupo_detalhes = GrupoCrediario.get_by_id(
            mov.grupo_crediario_id, current_user.id)
        mov.crediario_detalhes = Crediario.get_by_id(
            mov.crediario_id, current_user.id)
        # data_compra continua como data completa
        mov.data_compra_formatada = mov.data_compra.strftime(
            '%d/%m/%Y') if mov.data_compra else ''
        # primeira_parcela e ultima_parcela agora são formatadas diretamente no template para Mês/Ano
        # Não precisamos mais das variáveis _formatada aqui, pois o Jinja fará isso.

    return render_template('movimento_crediario/list.html', movimentos=movimentos)


@bp_movimento_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento_crediario():
    """
    Adiciona um novo movimento de crediário para o usuário logado.
    """
    grupos_crediario = GrupoCrediario.get_all_by_user(current_user.id)
    crediarios = Crediario.get_all_by_user(current_user.id)

    # Prepara a data atual para preencher o campo de data de compra
    today_date = date.today().isoformat()
    # Prepara o mês/ano atual para preencher o campo de primeira parcela (formato YYYY-MM)
    today_month_year = date.today().strftime('%Y-%m')

    if not grupos_crediario:
        flash('Precisa de registar pelo menos um Grupo de Crediário antes de adicionar um movimento.', 'warning')
        return redirect(url_for('grupo_crediario.add_grupo_crediario'))
    if not crediarios:
        flash('Precisa de registar pelo menos um Crediário antes de adicionar um movimento.', 'warning')
        return redirect(url_for('crediario.add_crediario'))

    if request.method == 'POST':
        grupo_crediario_id = request.form.get('grupo_crediario_id', type=int)
        crediario_id = request.form.get('crediario_id', type=int)
        data_compra_str = request.form.get('data_compra')
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total').replace(',', '.')
        num_parcelas_str = request.form.get('num_parcelas')
        primeira_parcela_month_year_str = request.form.get(
            'primeira_parcela')  # Agora é YYYY-MM

        try:
            data_compra = datetime.strptime(data_compra_str, '%Y-%m-%d').date()
            # Converte 'YYYY-MM' para um objeto date, usando o dia 1 como padrão
            primeira_parcela = datetime.strptime(
                primeira_parcela_month_year_str, '%Y-%m').date()

            valor_total = Decimal(valor_total_str)
            num_parcelas = int(num_parcelas_str)

            if num_parcelas <= 0 or num_parcelas > 360:
                raise ValueError(
                    "O número de parcelas deve ser entre 1 e 360.")
            if valor_total <= 0:
                raise ValueError("O valor total deve ser maior que zero.")

            MovimentoCrediario.add(
                user_id=current_user.id,
                grupo_crediario_id=grupo_crediario_id,
                crediario_id=crediario_id,
                data_compra=data_compra,
                descricao=descricao,
                valor_total=valor_total,
                num_parcelas=num_parcelas,
                primeira_parcela=primeira_parcela  # Passa o objeto date com dia 1
            )

            flash('Movimento de crediário adicionado com sucesso!', 'success')
            return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o movimento de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar movimento de crediário: {e}", exc_info=True)

    return render_template('movimento_crediario/add.html',
                           grupos_crediario=grupos_crediario,
                           crediarios=crediarios,
                           today_date=today_date,
                           today_month_year=today_month_year)  # Passa o mês/ano atual


@bp_movimento_crediario.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
@own_movement_crediario_required
def edit_movimento_crediario(movimento_id):
    """
    Edita um movimento de crediário existente.
    """
    movimento = MovimentoCrediario.get_by_id(movimento_id, current_user.id)
    if not movimento:
        flash('Movimento de crediário não encontrado.', 'danger')
        return redirect(url_for('movimento_crediario.list_movimentos_crediario'))

    grupos_crediario = GrupoCrediario.get_all_by_user(current_user.id)
    crediarios = Crediario.get_all_by_user(current_user.id)

    # Formata as datas para exibição no formulário (GET)
    data_compra_str = movimento.data_compra.strftime(
        '%Y-%m-%d') if isinstance(movimento.data_compra, (datetime, date)) else ''
    # Formata a primeira parcela para YYYY-MM para o input type="month"
    primeira_parcela_month_year = movimento.primeira_parcela.strftime(
        '%Y-%m') if isinstance(movimento.primeira_parcela, (datetime, date)) else ''

    if not grupos_crediario:
        flash('Precisa de registar pelo menos um Grupo de Crediário.', 'warning')
        return redirect(url_for('grupo_crediario.add_grupo_crediario'))
    if not crediarios:
        flash('Precisa de registar pelo menos um Crediário.', 'warning')
        return redirect(url_for('crediario.add_crediario'))

    if request.method == 'POST':
        grupo_crediario_id = request.form.get('grupo_crediario_id', type=int)
        crediario_id = request.form.get('crediario_id', type=int)
        data_compra_str = request.form.get('data_compra')
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total').replace(',', '.')
        num_parcelas_str = request.form.get('num_parcelas')
        primeira_parcela_month_year_str = request.form.get(
            'primeira_parcela')  # Agora é YYYY-MM

        try:
            data_compra = datetime.strptime(data_compra_str, '%Y-%m-%d').date()
            # Converte 'YYYY-MM' para um objeto date, usando o dia 1 como padrão
            primeira_parcela = datetime.strptime(
                primeira_parcela_month_year_str, '%Y-%m').date()

            valor_total = Decimal(valor_total_str)
            num_parcelas = int(num_parcelas_str)

            if num_parcelas <= 0 or num_parcelas > 360:
                raise ValueError(
                    "O número de parcelas deve ser entre 1 e 360.")
            if valor_total <= 0:
                raise ValueError("O valor total deve ser maior que zero.")

            updated_movimento = MovimentoCrediario.update(
                movimento_id=movimento_id,
                user_id=current_user.id,
                grupo_crediario_id=grupo_crediario_id,
                crediario_id=crediario_id,
                data_compra=data_compra,
                descricao=descricao,
                valor_total=valor_total,
                num_parcelas=num_parcelas,
                primeira_parcela=primeira_parcela  # Passa o objeto date com dia 1
            )
            if updated_movimento:
                flash('Movimento de crediário atualizado com sucesso!', 'success')
                return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
            else:
                flash('Erro ao atualizar movimento de crediário.', 'danger')
        except ValueError as e:
            flash(f'Erro de validação: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o movimento de crediário: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar movimento de crediário ID {movimento_id}: {e}", exc_info=True)

    return render_template('movimento_crediario/edit.html',
                           movimento=movimento,
                           grupos_crediario=grupos_crediario,
                           crediarios=crediarios,
                           data_compra_str=data_compra_str,
                           # Passa o mês/ano para preencher o input
                           primeira_parcela_month_year=primeira_parcela_month_year)


@bp_movimento_crediario.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
@own_movement_crediario_required
def delete_movimento_crediario(movimento_id):
    """
    Deleta um movimento de crediário. Apenas via POST para segurança.
    """
    try:
        if MovimentoCrediario.delete(movimento_id, current_user.id):
            flash('Movimento de crediário deletado com sucesso!', 'success')
        else:
            flash('Erro ao deletar movimento de crediário.', 'danger')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')
        current_app.logger.warning(
            f"Erro de validação ao deletar movimento de crediário ID {movimento_id} (UserID: {current_user.id}): {e}")
    except Exception as e:
        flash(
            f'Ocorreu um erro inesperado ao deletar o movimento de crediário: {e}', 'danger')
        current_app.logger.error(
            f"Erro inesperado ao deletar movimento de crediário ID {movimento_id} (UserID: {current_user.id}): {e}", exc_info=True)
    return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
