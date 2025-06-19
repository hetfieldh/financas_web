// static/js/main.js

// Este script é carregado em todas as páginas via base.html.
// Ele contém lógica global e funções utilitárias.

// --- Funções Auxiliares Globais ---
// Funções que podem ser úteis em qualquer parte do seu frontend.

/**
 * Restringe a entrada de um campo de texto apenas a dígitos inteiros.
 * @param {HTMLInputElement} inputElement O elemento de input a ser restringido.
 */
window.restrictToIntegers = function (inputElement) {
    inputElement.value = inputElement.value.replace(/[^0-9]/g, '');
};

/**
 * Restringe a entrada de um campo de texto a um formato de moeda (decimal).
 * Permite dígitos, vírgula, ponto e um único traço no início para valores negativos.
 * Limita a 2 casas decimais após o separador.
 * @param {HTMLInputElement} inputElement O elemento de input a ser restringido.
 */
window.restrictToCurrency = function (inputElement) {
    let value = inputElement.value;

    // Remove todos os caracteres que não sejam dígitos, vírgula, ponto ou traço
    let filteredValue = value.replace(/[^0-9.,-]/g, '');

    // Garante que o traço, se existir, seja apenas no início
    if (filteredValue.indexOf('-') > 0) {
        filteredValue = filteredValue.replace(/-/g, '');
        if (value.startsWith('-')) {
            filteredValue = '-' + filteredValue;
        }
    }

    // Lida com múltiplos separadores decimais (mantém apenas o último)
    const decimalSeparator = filteredValue.includes(',') ? ',' : filteredValue.includes('.') ? '.' : null;
    if (decimalSeparator) {
        const parts = filteredValue.split(decimalSeparator);
        if (parts.length > 2) { // Mais de um separador (ex: "1.234.56" ou "1,2,3,4")
            // Rejunta as partes dos milhares e mantém apenas o último separador decimal
            parts[0] = parts.slice(0, -1).join(''); // Junta tudo menos a última parte como inteira
            filteredValue = parts[0] + decimalSeparator + parts[parts.length - 1];
        }
        // Limita a 2 casas decimais após o separador
        const finalParts = filteredValue.split(decimalSeparator);
        if (finalParts.length > 1) {
            finalParts[1] = finalParts[1].substring(0, 2);
            filteredValue = finalParts[0] + decimalSeparator + finalParts[1];
        }
    }

    inputElement.value = filteredValue;
};

/**
 * Converte uma string formatada para exibição (ex: "1.234,56") em um número float.
 * @param {string} valueString A string de valor a ser parseada.
 * @returns {number} O valor numérico parseado.
 */
function parseDisplayValue(valueString) {
    if (!valueString) return NaN;
    valueString = valueString.trim();
    // Remove pontos de milhares e substitui vírgula decimal por ponto
    valueString = valueString.replace(/\./g, '').replace(/,/g, '.');
    return parseFloat(valueString);
}

/**
 * Formata um número para exibição no formato de moeda (ex: "1.234,56").
 * @param {number} number O número a ser formatado.
 * @returns {string} A string formatada.
 */
function formatDisplayValue(number) {
    if (isNaN(number)) return '';
    // Garante que a formatação do sinal esteja correta
    const sign = number < 0 ? '-' : '';
    const absNumber = Math.abs(number);
    // Usa toLocaleString para formatação de moeda com vírgula como separador decimal
    // ou fallback para replace se toLocaleString não for o comportamento desejado.
    return sign + absNumber.toFixed(2).replace('.', ',');
}

/**
 * Função utilitária para decodificar dados JSON Base64 de um elemento script.
 * @param {string} elementId O ID do elemento script que contém os dados Base64.
 * @param {string} contextName Nome para logs de erro (ex: 'add.html').
 * @returns {Array} O array de dados JSON decodificados.
 */
function decodeBase64JsonData(elementId, contextName = '') {
    const jsonScriptTag = document.getElementById(elementId);
    if (!jsonScriptTag || !jsonScriptTag.textContent) {
        console.warn(`Elemento '${elementId}' não encontrado ou sem conteúdo no contexto ${contextName}.`);
        return [];
    }

    try {
        let base64StringRaw = jsonScriptTag.textContent;
        // Remove espaços em branco e caracteres não-base64
        const base64StringClean = base64StringRaw.replace(/\s/g, '').replace(/[^A-Za-z0-9+/=]/g, '');

        // Adiciona preenchimento '=' se necessário
        const padding = base64StringClean.length % 4;
        const base64StringPadded = padding === 0 ? base64StringClean : base64StringClean + '='.repeat(4 - padding);

        if (!base64StringPadded) {
            console.warn(`Base64 string vazia após limpeza e preenchimento no contexto ${contextName}.`);
            return [];
        }

        const jsonString = atob(base64StringPadded);
        return JSON.parse(jsonString);
    } catch (e) {
        console.error(`Erro ao decodificar/analisar JSON Base64 do elemento '${elementId}' no contexto ${contextName}:`, e);
        return [];
    }
}


// --- Funções de Inicialização de Páginas Específicas ---
// Estas funções serão chamadas apenas se o elemento com o ID correspondente existir no DOM.
// Isso evita a execução de código desnecessário em páginas onde ele não é relevante.

/**
 * Inicializa a lógica específica para páginas de Movimento de Renda (add/edit).
 */
function initMovimentoRendaPage() {
    const valorDisplayInput = document.getElementById('valor_display');
    const valorHiddenInput = document.getElementById('valor');
    const rendaIdSelect = document.getElementById('renda_id');
    const valorValidationMessage = document.getElementById('valor-validation-message');

    // Se os elementos necessários não existirem, não execute a lógica desta página.
    if (!valorDisplayInput || !valorHiddenInput || !rendaIdSelect || !valorValidationMessage) {
        // console.log("Elementos para Movimento de Renda não encontrados, ignorando inicialização.");
        return;
    }

    const rendasData = decodeBase64JsonData('rendas-data', 'Movimento de Renda');
    const rendasTypesMap = {};
    rendasData.forEach(item => {
        rendasTypesMap[item.id] = { descricao: item.descricao, tipo: item.tipo };
    });

    /**
     * Valida e ajusta o valor do input com base no tipo de renda selecionado.
     */
    function validateAndAdjustValorRenda() {
        let numericValue = parseDisplayValue(valorDisplayInput.value);

        const selectedRendaId = rendaIdSelect.value;
        let rendaTipo = null;
        if (selectedRendaId && rendasTypesMap[selectedRendaId]) {
            rendaTipo = rendasTypesMap[selectedRendaId].tipo;
        }

        valorValidationMessage.classList.add('hidden');
        valorDisplayInput.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');

        if (isNaN(numericValue)) {
            if (valorDisplayInput.value !== '' && valorDisplayInput.value !== '-') {
                valorValidationMessage.textContent = 'Por favor, insira um valor numérico válido (ex: 1.500,75 ou -50,00).';
                valorValidationMessage.classList.remove('hidden');
                valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            }
            numericValue = 0;
        }

        // Lógica para ajustar o sinal do valor com base no tipo de Renda
        if (rendaTipo === 'Provento' || rendaTipo === 'Benefício') {
            if (numericValue < 0) {
                numericValue = Math.abs(numericValue);
                valorValidationMessage.textContent = 'Para Proventos ou Benefícios, o valor deve ser positivo. Valor ajustado.';
                valorValidationMessage.classList.remove('hidden');
                valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            }
        } else if (rendaTipo === 'Desconto') {
            if (numericValue > 0) {
                numericValue = -Math.abs(numericValue);
                valorValidationMessage.textContent = 'Para Descontos, o valor deve ser negativo. Valor ajustado.';
                valorValidationMessage.classList.remove('hidden');
                valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            }
        }

        valorDisplayInput.value = formatDisplayValue(numericValue);
        valorHiddenInput.value = numericValue.toFixed(2);
    }

    // Adiciona listeners para eventos
    valorDisplayInput.addEventListener('input', function () {
        window.restrictToCurrency(this); // Usa a função global para restrição de formato
    });

    valorDisplayInput.addEventListener('blur', validateAndAdjustValorRenda);

    valorDisplayInput.addEventListener('focus', function () {
        const currentNumericValue = parseDisplayValue(this.value);
        if (!isNaN(currentNumericValue)) {
            this.value = currentNumericValue.toString();
        } else {
            this.value = '';
        }
        valorValidationMessage.classList.add('hidden');
        valorDisplayInput.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    });

    rendaIdSelect.addEventListener('change', validateAndAdjustValorRenda);

    // Inicializa o campo de valor na carga da página
    // Usa o valor do campo hidden se estiver preenchido para evitar problemas de formatação inicial
    const initialNumericValue = parseDisplayValue(valorHiddenInput.value);

    if (!isNaN(initialNumericValue)) {
        valorDisplayInput.value = formatDisplayValue(initialNumericValue);
        validateAndAdjustValorRenda(); // Aplica a validação inicial para garantir o sinal correto
    } else {
        valorDisplayInput.value = formatDisplayValue(0);
        valorHiddenInput.value = "0.00";
    }
}

/**
 * Inicializa a lógica específica para páginas de Movimento de Transação (add/edit).
 */
function initMovimentoTransacaoPage() {
    const valorDisplayInput = document.getElementById('valor_display');
    const valorHiddenInput = document.getElementById('valor');
    const tipoMovimentoDisplay = document.getElementById('tipo_movimento_display');
    const tipoMovimentoHidden = document.getElementById('tipo_hidden');
    const transacaoBancariaIdSelect = document.getElementById('transacao_bancaria_id');
    const valorValidationMessage = document.getElementById('valor-validation-message');

    // Se os elementos necessários não existirem, não execute a lógica desta página.
    if (!valorDisplayInput || !valorHiddenInput || !tipoMovimentoDisplay || !tipoMovimentoHidden || !transacaoBancariaIdSelect || !valorValidationMessage) {
        // console.log("Elementos para Movimento de Transação não encontrados, ignorando inicialização.");
        return;
    }

    const transacoesData = decodeBase64JsonData('transacoes-data', 'Movimento de Transação');
    const transactionTypesMap = {};
    transacoesData.forEach(item => {
        transactionTypesMap[item.id] = { transacao: item.transacao, tipo: item.tipo };
    });

    /**
     * Ajusta o campo 'tipo_movimento_display' e 'tipo_hidden' com base no valor.
     * @param {string} forcedType Tipo de movimento a ser forçado ('Receita' ou 'Despesa').
     */
    function adjustTipoMovimento(forcedType = null) {
        if (forcedType) {
            tipoMovimentoDisplay.value = forcedType;
            tipoMovimentoHidden.value = forcedType;
        } else {
            const valorNumerico = parseDisplayValue(valorDisplayInput.value);
            if (!isNaN(valorNumerico)) {
                tipoMovimentoDisplay.value = valorNumerico >= 0 ? 'Receita' : 'Despesa';
                tipoMovimentoHidden.value = valorNumerico >= 0 ? 'Receita' : 'Despesa';
            } else {
                tipoMovimentoDisplay.value = 'Receita'; // Default se o valor não for um número
                tipoMovimentoHidden.value = 'Receita';
            }
        }
    }

    /**
     * Valida e ajusta o valor do input com base no tipo de transação selecionado.
     */
    function validateAndAdjustValorTransacao() {
        let numericValue = parseDisplayValue(valorDisplayInput.value);

        const selectedTransacaoId = transacaoBancariaIdSelect.value;
        let transacaoTipo = null;
        if (selectedTransacaoId && transactionTypesMap[selectedTransacaoId]) {
            transacaoTipo = transactionTypesMap[selectedTransacaoId].tipo;
        }

        valorValidationMessage.classList.add('hidden');
        valorDisplayInput.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');

        if (isNaN(numericValue)) {
            if (valorDisplayInput.value !== '' && valorDisplayInput.value !== '-') {
                valorValidationMessage.textContent = 'Por favor, insira um valor numérico válido (ex: 1.500,75 ou -50,00).';
                valorValidationMessage.classList.remove('hidden');
                valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            }
            numericValue = 0;
        }

        if (transacaoTipo === 'Crédito' && numericValue < 0) {
            numericValue = Math.abs(numericValue);
            valorValidationMessage.textContent = 'Para transações de Crédito, o valor deve ser positivo. Valor ajustado.';
            valorValidationMessage.classList.remove('hidden');
            valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        } else if (transacaoTipo === 'Débito' && numericValue > 0) {
            numericValue = -Math.abs(numericValue);
            valorValidationMessage.textContent = 'Para transações de Débito, o valor deve ser negativo. Valor ajustado.';
            valorValidationMessage.classList.remove('hidden');
            valorDisplayInput.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        }

        valorDisplayInput.value = formatDisplayValue(numericValue);
        valorHiddenInput.value = numericValue.toFixed(2);
        adjustTipoMovimento(numericValue >= 0 ? 'Receita' : 'Despesa'); // Ajusta o tipo após ajustar o valor
    }

    // Adiciona listeners para eventos
    valorDisplayInput.addEventListener('input', function () {
        window.restrictToCurrency(this);
    });

    valorDisplayInput.addEventListener('blur', validateAndAdjustValorTransacao);

    valorDisplayInput.addEventListener('focus', function () {
        const currentNumericValue = parseDisplayValue(this.value);
        if (!isNaN(currentNumericValue)) {
            this.value = currentNumericValue.toString();
        } else {
            this.value = '';
        }
        valorValidationMessage.classList.add('hidden');
        valorDisplayInput.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    });

    transacaoBancariaIdSelect.addEventListener('change', validateAndAdjustValorTransacao);

    // Inicializa o campo de valor na carga da página
    const initialNumericValue = parseDisplayValue(valorHiddenInput.value);

    if (!isNaN(initialNumericValue)) {
        valorDisplayInput.value = formatDisplayValue(initialNumericValue);
        validateAndAdjustValorTransacao(); // Aplica a validação inicial para garantir o sinal correto
    } else {
        valorDisplayInput.value = formatDisplayValue(0);
        valorHiddenInput.value = "0.00";
    }
    adjustTipoMovimento(initialNumericValue >= 0 ? 'Receita' : 'Despesa'); // Ajusta o tipo inicial
}


// --- Lógica de Inicialização Principal (DOMContentLoaded) ---
document.addEventListener('DOMContentLoaded', function () {
    // 1. Inicialização do Menu Mobile (comum a todas as páginas)
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // 2. Aplicação de restrições de input para campos de Conta Bancária (comum a add/edit de conta)
    // Usando uma função para aplicar listeners de forma genérica
    function applyInputRestrictions(elementId, restrictionFunction) {
        const inputElement = document.getElementById(elementId);
        if (inputElement) {
            inputElement.addEventListener('input', function () {
                restrictionFunction(this);
            });
        }
    }

    applyInputRestrictions('agencia', window.restrictToIntegers);
    applyInputRestrictions('conta', window.restrictToIntegers);
    applyInputRestrictions('saldo_inicial', window.restrictToCurrency);
    applyInputRestrictions('saldo_atual', window.restrictToCurrency);
    applyInputRestrictions('limite', window.restrictToCurrency);
    applyInputRestrictions('valor_total', window.restrictToCurrency); // Para o 'valor_total' que aparece duas vezes no seu original


    // 3. Inicialização de lógicas específicas de formulário
    // Chamamos as funções específicas apenas se os elementos que elas precisam existirem no DOM.
    // Isso é mais eficiente do que verificar dentro de cada função específica.

    // Verifica se estamos em uma página de Movimento de Renda (add ou edit)
    if (document.getElementById('renda_id') && document.getElementById('valor_display') && document.getElementById('valor')) {
        initMovimentoRendaPage();
    }

    // Verifica se estamos em uma página de Movimento de Transação (add ou edit)
    // O ID 'transacao_bancaria_id' é um bom indicador
    if (document.getElementById('transacao_bancaria_id') && document.getElementById('valor_display') && document.getElementById('valor')) {
        initMovimentoTransacaoPage();
    }

});