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

# Cria um Blueprint para organizar as rotas relacionadas a movimentos de credi\u00e1rio
bp_movimento_crediario = Blueprint(
    'movimento_crediario', __name__, url_prefix='/movimentos_crediario')


def own_movement_crediario_required(f):
    """
    Decorador personalizado para garantir que o usu\u00e1rio est\u00e1 acessando ou modificando
    seu pr\u00f3prio movimento de credi\u00e1rio.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_id = kwargs.get('movimento_id')
        if movimento_id:
            movimento = MovimentoCrediario.get_by_id(
                movimento_id, current_user.id)
            if not movimento:
                flash('Movimento de credi\u00e1rio n\u00e3o encontrado ou voc\u00ea n\u00e3o tem permiss\u00e3o para acess\u00e1-lo.', 'danger')
                return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_crediario.route('/')
@login_required
def list_movimentos_crediario():
    """
    Lista todos os movimentos de credi\u00e1rio do usu\u00e1rio logado.
    Para exibir detalhes do grupo e credi\u00e1rio, buscamos os objetos completos.
    """
    movimentos = MovimentoCrediario.get_all_by_user(current_user.id)
    for mov in movimentos:
        mov.grupo_detalhes = GrupoCrediario.get_by_id(
            mov.grupo_crediario_id, current_user.id)
        mov.crediario_detalhes = Crediario.get_by_id(
            mov.crediario_id, current_user.id)
        # Formata as datas para exibi\u00e7\u00e3o
        mov.data_compra_formatada = mov.data_compra.strftime(
            '%d/%m/%Y') if mov.data_compra else ''
        mov.primeira_parcela_formatada = mov.primeira_parcela.strftime(
            '%d/%m/%Y') if mov.primeira_parcela else ''
        mov.ultima_parcela_formatada = mov.ultima_parcela.strftime(
            '%d/%m/%Y') if mov.ultima_parcela else ''

    return render_template('movimento_crediario/list.html', movimentos=movimentos)


@bp_movimento_crediario.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento_crediario():
    """
    Adiciona um novo movimento de credi\u00e1rio para o usu\u00e1rio logado.
    """
    grupos_crediario = GrupoCrediario.get_all_by_user(current_user.id)
    crediarios = Crediario.get_all_by_user(current_user.id)

    # Prepara a data de hoje para o valor predefinido do campo de data
    today_date = date.today().isoformat()  # Formato 'YYYY-MM-DD'

    if not grupos_crediario:
        flash('Precisa de registar pelo menos um Grupo de Credi\u00e1rio antes de adicionar um movimento.', 'warning')
        return redirect(url_for('grupo_crediario.add_grupo_crediario'))
    if not crediarios:
        flash('Precisa de registar pelo menos um Credi\u00e1rio antes de adicionar um movimento.', 'warning')
        return redirect(url_for('crediario.add_crediario'))

    if request.method == 'POST':
        grupo_crediario_id = request.form.get('grupo_crediario_id', type=int)
        crediario_id = request.form.get('crediario_id', type=int)
        data_compra_str = request.form.get('data_compra')
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total').replace(',', '.')
        num_parcelas_str = request.form.get('num_parcelas')
        primeira_parcela_str = request.form.get('primeira_parcela')

        try:
            data_compra = datetime.strptime(data_compra_str, '%Y-%m-%d').date()
            primeira_parcela = datetime.strptime(
                primeira_parcela_str, '%Y-%m-%d').date()
            valor_total = Decimal(valor_total_str)
            num_parcelas = int(num_parcelas_str)

            if num_parcelas <= 0 or num_parcelas > 360:
                raise ValueError(
                    "O n\u00famero de parcelas deve ser entre 1 e 360.")
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
                primeira_parcela=primeira_parcela
            )

            flash('Movimento de credi\u00e1rio adicionado com sucesso!', 'success')
            return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao adicionar o movimento de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao adicionar movimento de credi\u00e1rio: {e}", exc_info=True)

    return render_template('movimento_crediario/add.html',
                           grupos_crediario=grupos_crediario,
                           crediarios=crediarios,
                           today_date=today_date)


@bp_movimento_crediario.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 edita seus pr\u00f3prios movimentos
@own_movement_crediario_required
def edit_movimento_crediario(movimento_id):
    """
    Edita um movimento de credi\u00e1rio existente.
    """
    movimento = MovimentoCrediario.get_by_id(movimento_id, current_user.id)
    if not movimento:
        flash('Movimento de credi\u00e1rio n\u00e3o encontrado.', 'danger')
        return redirect(url_for('movimento_crediario.list_movimentos_crediario'))

    grupos_crediario = GrupoCrediario.get_all_by_user(current_user.id)
    crediarios = Crediario.get_all_by_user(current_user.id)

    # Formata as datas para o valor predefinido do campo de data
    data_compra_str = movimento.data_compra.strftime(
        '%Y-%m-%d') if isinstance(movimento.data_compra, (datetime, date)) else ''
    primeira_parcela_str = movimento.primeira_parcela.strftime(
        '%Y-%m-%d') if isinstance(movimento.primeira_parcela, (datetime, date)) else ''

    if not grupos_crediario:
        flash('Precisa de registar pelo menos um Grupo de Credi\u00e1rio.', 'warning')
        return redirect(url_for('grupo_crediario.add_grupo_crediario'))
    if not crediarios:
        flash('Precisa de registar pelo menos um Credi\u00e1rio.', 'warning')
        return redirect(url_for('crediario.add_crediario'))

    if request.method == 'POST':
        grupo_crediario_id = request.form.get('grupo_crediario_id', type=int)
        crediario_id = request.form.get('crediario_id', type=int)
        data_compra_str = request.form.get('data_compra')
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total').replace(',', '.')
        num_parcelas_str = request.form.get('num_parcelas')
        primeira_parcela_str = request.form.get('primeira_parcela')

        try:
            data_compra = datetime.strptime(data_compra_str, '%Y-%m-%d').date()
            primeira_parcela = datetime.strptime(
                primeira_parcela_str, '%Y-%m-%d').date()
            valor_total = Decimal(valor_total_str)
            num_parcelas = int(num_parcelas_str)

            if num_parcelas <= 0 or num_parcelas > 360:
                raise ValueError(
                    "O n\u00famero de parcelas deve ser entre 1 e 360.")
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
                primeira_parcela=primeira_parcela
            )
            if updated_movimento:
                flash('Movimento de credi\u00e1rio atualizado com sucesso!', 'success')
                return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
            else:
                flash('Erro ao atualizar movimento de credi\u00e1rio.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(
                f'Ocorreu um erro ao atualizar o movimento de credi\u00e1rio: {e}', 'danger')
            current_app.logger.error(
                f"Erro ao atualizar movimento de credi\u00e1rio ID {movimento_id}: {e}", exc_info=True)

    return render_template('movimento_crediario/edit.html',
                           movimento=movimento,
                           grupos_crediario=grupos_crediario,
                           crediarios=crediarios,
                           data_compra_str=data_compra_str,
                           primeira_parcela_str=primeira_parcela_str)


@bp_movimento_crediario.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
# Garante que o usu\u00e1rio s\u00f3 deleta seus pr\u00f3prios movimentos
@own_movement_crediario_required
def delete_movimento_crediario(movimento_id):
    """
    Deleta um movimento de credi\u00e1rio. Apenas via POST para seguran\u00e7a.
    """
    if MovimentoCrediario.delete(movimento_id, current_user.id):
        flash('Movimento de credi\u00e1rio deletado com sucesso!', 'success')
    else:
        flash('Erro ao deletar movimento de credi\u00e1rio.', 'danger')
    return redirect(url_for('movimento_crediario.list_movimentos_crediario'))
