// static/js/main.js

// Este script é carregado em todas as páginas via base.html.
// Adicione aqui qualquer lógica JavaScript global ou de inicialização.

document.addEventListener('DOMContentLoaded', function () {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // --- Funções para restrição de entrada de dados ---

    window.restrictToIntegers = function (inputElement) {
        inputElement.value = inputElement.value.replace(/[^0-9]/g, '');
    };

    // Restringe a entrada a números decimais no formato de moeda (permite , ou .)
    // e limita a 2 casas decimais.
    window.restrictToCurrency = function (inputElement) {
        let value = inputElement.value;

        // Permite apenas dígitos, vírgulas e pontos
        value = value.replace(/[^0-9.,]/g, '');

        // Lida com múltiplos separadores decimais (mantém apenas o primeiro)
        if ((value.match(/,/g) || []).length > 1) {
            value = value.replace(/,(.*?),/g, '$1'); 
        }
        if ((value.match(/\./g) || []).length > 1) {
            value = value.replace(/\.(.*?)\./g, '$1');
        }

        // Se houver um separador decimal, limita a 2 casas decimais
        let parts;
        if (value.includes(',')) {
            parts = value.split(',');
            if (parts.length > 1) {
                parts[1] = parts[1].substring(0, 2);
                value = parts[0] + ',' + parts[1];
            }
        } else if (value.includes('.')) {
            parts = value.split('.');
            if (parts.length > 1) {
                parts[1] = parts[1].substring(0, 2);
                value = parts[0] + '.' + parts[1];
            }
        }

        inputElement.value = value;
    };

    // --- Aplica as restrições aos campos do formulário de Conta Bancária ---
    // (Estas restrições serão aplicadas a ambos os templates add.html e edit.html se tiverem os mesmos IDs)

    const agenciaInput = document.getElementById('agencia');
    if (agenciaInput) {
        agenciaInput.addEventListener('input', function () {
            window.restrictToIntegers(this);
        });
    }

    const contaInput = document.getElementById('conta');
    if (contaInput) {
        contaInput.addEventListener('input', function () {
            window.restrictToIntegers(this);
        });
    }

    const saldoInicialInput = document.getElementById('saldo_inicial');
    if (saldoInicialInput) {
        saldoInicialInput.addEventListener('input', function () {
            window.restrictToCurrency(this);
        });
    }

    const saldoAtualInput = document.getElementById('saldo_atual');
    if (saldoAtualInput) {
        saldoAtualInput.addEventListener('input', function () {
            window.restrictToCurrency(this);
        });
    }

    const limiteInput = document.getElementById('limite');
    if (limiteInput) {
        limiteInput.addEventListener('input', function () {
            window.restrictToCurrency(this);
        });
    }

});
