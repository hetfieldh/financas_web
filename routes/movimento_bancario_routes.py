import json
import base64
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.movimento_bancario_model import MovimentoBancario
from models.conta_bancaria_model import ContaBancaria
from models.transacao_bancaria_model import TransacaoBancaria
from functools import wraps
from datetime import datetime, date
from decimal import Decimal # Importa o tipo Decimal para c\u00e1lculos monet\u00e1rios precisos

# Cria um Blueprint para organizar as rotas relacionadas a movimentos banc\u00e1rios
# Verificado para problemas de importação, definição de blueprint no nível superior.
bp_movimento_bancario = Blueprint('movimento_bancario', __name__, url_prefix='/movimentos')

# Defini\u00e7\u00f5es de tipos de movimento para o formul\u00e1rio
TIPOS_MOVIMENTO = ["Despesa", "Receita"]

def own_movement_required(f):
    """
    Decorador personalizado para garantir que o utilizador est\u00e1 a aceder ou a modificar
    o seu pr\u00f3prio movimento banc\u00e1rio.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        movimento_id = kwargs.get('movimento_id')
        if movimento_id:
            movimento = MovimentoBancario.get_by_id(movimento_id, current_user.id)
            if not movimento:
                flash('Movimento banc\u00e1rio n\u00e3o encontrado ou n\u00e3o tem permiss\u00e3o para aceder a ele.', 'danger')
                return redirect(url_for('movimento_bancario.list_movimentos'))
        return f(*args, **kwargs)
    return decorated_function


@bp_movimento_bancario.route('/')
@login_required
def list_movimentos():
    """
    Lista todos os movimentos banc\u00e1rios do utilizador autenticado.
    Para exibir detalhes da conta e transa\u00e7\u00e3o, buscamos os objetos completos.
    """
    movimentos = MovimentoBancario.get_all_by_user(current_user.id)
    # Para cada movimento, buscamos os objetos de ContaBancaria e TransacaoBancaria
    # Isso pode ser otimizado com joins na query SQL se o n\u00famero de movimentos for muito grande.
    # Por enquanto, faremos buscas individuais para simplicidade.
    for mov in movimentos:
        mov.conta_detalhes = ContaBancaria.get_by_id(mov.conta_bancaria_id, current_user.id)
        mov.transacao_detalhes = TransacaoBancaria.get_by_id(mov.transacao_bancaria_id, current_user.id)
        # Formata a data para exibi\u00e7\u00e3o
        mov.data_formatada = mov.data.strftime('%d/%m/%Y') if mov.data else ''

    return render_template('movimento_bancario/list.html', movimentos=movimentos)


@bp_movimento_bancario.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento():
    """
    Adiciona um novo movimento banc\u00e1rio para o utilizador autenticado.
    """
    contas = ContaBancaria.get_all_by_user(current_user.id)
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)

    # Prepara os dados das transa\u00e7\u00f5es e codifica em Base64
    transacoes_json_data = [{'id': t.id, 'transacao': t.transacao, 'tipo': t.tipo} for t in transacoes]
    transacoes_json_string = json.dumps(transacoes_json_data)
    transacoes_base64_string = base64.b64encode(transacoes_json_string.encode('utf-8')).decode('utf-8')

    # Prepara a data de hoje para o valor predefinido do campo de data
    today_date = date.today().isoformat() # Formato 'YYYY-MM-DD'

    if not contas:
        flash('Precisa de registar pelo menos uma conta banc\u00e1ria antes de adicionar um movimento.', 'warning')
        return redirect(url_for('conta_bancaria.add_conta'))
    if not transacoes:
        flash('Precisa de registar pelo menos um tipo de transa\u00e7\u00e3o banc\u00e1ria (Cr\u00e9dito/D\u00e9bito) antes de adicionar um movimento.', 'warning')
        return redirect(url_for('transacao_bancaria.add_transacao'))

    if request.method == 'POST':
        conta_bancaria_id = request.form.get('conta_bancaria_id', type=int)
        transacao_bancaria_id = request.form.get('transacao_bancaria_id', type=int)
        data_str = request.form.get('data')
        valor_str = request.form.get('valor') # J\u00e1 \u00e9 limpo de ', ' e tem '.' no frontend
        tipo = request.form.get('tipo_hidden') # Pega do campo oculto

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
            valor = Decimal(valor_str) # Converte para Decimal

            # Valida\u00e7\u00f5es de backend para o valor e tipo de transa\u00e7\u00e3o
            selected_transacao = TransacaoBancaria.get_by_id(transacao_bancaria_id, current_user.id)
            if not selected_transacao:
                flash('Transa\u00e7\u00e3o selecionada n\u00e3o encontrada ou n\u00e3o lhe pertence.', 'danger')
                return render_template('movimento_bancario/add.html',
                                       contas=contas, transacoes=transacoes,
                                       TIPOS_MOVIMENTO=TIPOS_MOVIMENTO, today_date=today_date,
                                       transacoes_json_data=transacoes_base64_string)

            if (selected_transacao.tipo == 'Cr\u00e9dito' and valor < 0) or \
               (selected_transacao.tipo == 'D\u00e9bito' and valor > 0):
                flash(f'O valor introduzido ({valor_str}) \u00e9 inv\u00e1lido para o tipo de transa\u00e7\u00e3o "{selected_transacao.tipo}".', 'danger')
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
            
            # REMOVIDO: A lógica de atualização de saldo foi movida para o modelo MovimentoBancario
            # para centralizar a responsabilidade e evitar duplicações.

            flash('Movimento banc\u00e1rio adicionado com sucesso!', 'success')
            return redirect(url_for('movimento_bancario.list_movimentos'))
        except ValueError as e: # Captura ValueErrors do modelo (incluindo viola\u00e7\u00e3o de limite)
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(f'Ocorreu um erro ao adicionar o movimento banc\u00e1rio: {e}', 'danger')
            current_app.logger.error(f"Erro ao adicionar movimento banc\u00e1rio: {e}", exc_info=True)

    return render_template('movimento_bancario/add.html',
                           contas=contas, transacoes=transacoes,
                           TIPOS_MOVIMENTO=TIPOS_MOVIMENTO, today_date=today_date,
                           transacoes_json_data=transacoes_base64_string)


@bp_movimento_bancario.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
@own_movement_required # Garante que o utilizador s\u00f3 edita os seus pr\u00f3prios movimentos
def edit_movimento(movimento_id):
    """
    Edita um movimento banc\u00e1rio existente.
    """
    movimento = MovimentoBancario.get_by_id(movimento_id, current_user.id)
    if not movimento:
        flash('Movimento banc\u00e1rio n\u00e3o encontrado.', 'danger')
        return redirect(url_for('movimento_bancario.list_movimentos'))

    contas = ContaBancaria.get_all_by_user(current_user.id)
    transacoes = TransacaoBancaria.get_all_by_user(current_user.id)

    # Prepara os dados das transa\u00e7\u00f5es e codifica em Base64
    transacoes_json_data = [{'id': t.id, 'transacao': t.transacao, 'tipo': t.tipo} for t in transacoes]
    transacoes_json_string = json.dumps(transacoes_json_data)
    transacoes_base64_string = base64.b64encode(transacoes_json_string.encode('utf-8')).decode('utf-8')

    # Prepara a data do movimento para o valor predefinido do campo de data
    movimento_date_str = movimento.data.strftime('%Y-%m-%d') if isinstance(movimento.data, (datetime, date)) else ''

    if not contas:
        flash('Precisa de registar pelo menos uma conta banc\u00e1ria.', 'warning')
        return redirect(url_for('conta_bancaria.add_conta'))
    if not transacoes:
        flash('Precisa de registar pelo menos um tipo de transa\u00e7\u00e3o banc\u00e1ria.', 'warning')
        return redirect(url_for('transacao_bancaria.add_transacao'))

    if request.method == 'POST':
        conta_bancaria_id = request.form.get('conta_bancaria_id', type=int)
        transacao_bancaria_id = request.form.get('transacao_bancaria_id', type=int)
        data_str = request.form.get('data')
        valor_str = request.form.get('valor') # J\u00e1 \u00e9 limpo de ', ' e tem '.' no frontend
        tipo = request.form.get('tipo_hidden') # Pega do campo oculto

        # Obter o movimento original antes da atualiza\u00e7\u00e3o
        original_movimento = MovimentoBancario.get_by_id(movimento_id, current_user.id)

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
            valor = Decimal(valor_str) # Converte para Decimal

            # Valida\u00e7\u00f5es de backend para o valor e tipo de transa\u00e7\u00e3o
            selected_transacao = TransacaoBancaria.get_by_id(transacao_bancaria_id, current_user.id)
            if not selected_transacao:
                flash('Transa\u00e7\u00e3o selecionada n\u00e3o encontrada ou n\u00e3o lhe pertence.', 'danger')
                return render_template('movimento_bancario/edit.html',
                                       movimento=movimento, contas=contas,
                                       transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                                       movimento_date_str=movimento_date_str,
                                       transacoes_json_data=transacoes_base64_string)

            if (selected_transacao.tipo == 'Cr\u00e9dito' and valor < 0) or \
               (selected_transacao.tipo == 'D\u00e9bito' and valor > 0):
                flash(f'O valor introduzido ({valor_str}) \u00e9 inv\u00e1lido para o tipo de transa\u00e7\u00e3o "{selected_transacao.tipo}".', 'danger')
                return render_template('movimento_bancario/edit.html',
                                       movimento=movimento, contas=contas,
                                       transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                                       movimento_date_str=movimento_date_str,
                                       transacoes_json_data=transacoes_base64_string)

            updated_movimento = MovimentoBancario.update(
                movimento_id=movimento_id,
                user_id=current_user.id,
                conta_bancaria_id=conta_bancaria_id,
                transacao_bancaria_id=transacao_bancaria_id,
                data=data,
                valor=valor,
                tipo=tipo
            )
            if updated_movimento:
                # REMOVIDO: A lógica de atualização de saldo foi movida para o modelo MovimentoBancario
                # para centralizar a responsabilidade e evitar duplicações.

                flash('Movimento banc\u00e1rio atualizado com sucesso!', 'success')
                return redirect(url_for('movimento_bancario.list_movimentos'))
            else:
                flash('Erro ao atualizar movimento banc\u00e1rio.', 'danger')
        except ValueError as e:
            flash(f'Erro de valida\u00e7\u00e3o: {e}', 'danger')
        except Exception as e:
            flash(f'Ocorreu um erro ao atualizar o movimento banc\u00e1rio: {e}', 'danger')
            current_app.logger.error(f"Erro ao atualizar movimento banc\u00e1rio ID {movimento_id}: {e}", exc_info=True)

    return render_template('movimento_bancario/edit.html',
                           movimento=movimento, contas=contas,
                           transacoes=transacoes, TIPOS_MOVIMENTO=TIPOS_MOVIMENTO,
                           movimento_date_str=movimento_date_str,
                           transacoes_json_data=transacoes_base64_string)


@bp_movimento_bancario.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
@own_movement_required # Garante que o utilizador s\u00f3 deleta os seus pr\u00f3prios movimentos
def delete_movimento(movimento_id):
    """
    Deleta um movimento banc\u00e1rio. Apenas via POST para seguran\u00e7a.
    """
    # Obter o movimento antes de delet\u00e1-lo para reverter o saldo da conta
    movimento_a_deletar = MovimentoBancario.get_by_id(movimento_id, current_user.id)
    if not movimento_a_deletar:
        flash('Movimento banc\u00e1rio n\u00e3o encontrado para dele\u00e7\u00e3o.', 'danger')
        return redirect(url_for('movimento_bancario.list_movimentos'))

    try:
        if MovimentoBancario.delete(movimento_id, current_user.id):
            # REMOVIDO: A lógica de reversão de saldo foi movida para o modelo MovimentoBancario
            # para centralizar a responsabilidade e evitar duplicações.
            
            flash('Movimento banc\u00e1rio deletado com sucesso!', 'success')
        else:
            flash('Erro ao deletar movimento banc\u00e1rio.', 'danger')
    except ValueError as e:
        flash(f'Erro ao deletar movimento: {e}', 'danger')
    except Exception as e:
        flash(f'Ocorreu um erro inesperado ao tentar deletar o movimento banc\u00e1rio: {e}', 'danger')
        current_app.logger.error(f"Erro ao deletar movimento banc\u00e1rio ID {movimento_id}: {e}", exc_info=True)
    return redirect(url_for('movimento_bancario.list_movimentos'))
