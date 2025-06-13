// Este script é carregado em todas as páginas via base.html.
// Adicione aqui qualquer lógica JavaScript global ou de inicialização.

document.addEventListener('DOMContentLoaded', function () {
    // Exemplo de script: gerenciamento de menu mobile (já no _navbar.html, mas mantido aqui para ilustração)
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            // Alterna a classe 'hidden' para mostrar/esconder o menu mobile
            mobileMenu.classList.toggle('hidden');
        });
    }

    // --- Fun\u00e7\u00f5es para restri\u00e7\u00e3o de entrada de dados ---

    // Restringe a entrada a n\u00fameros inteiros (0-9)
    window.restrictToIntegers = function (inputElement) {
        inputElement.value = inputElement.value.replace(/[^0-9]/g, '');
    };

    // Restringe a entrada a n\u00fameros decimais no formato de moeda (permite , ou .)
    // e limita a 2 casas decimais.
    window.restrictToCurrency = function (inputElement) {
        let value = inputElement.value;

        // Permite apenas d\u00edgitos, v\u00edrgulas e pontos
        value = value.replace(/[^0-9.,]/g, '');

        // Lida com m\u00faltiplos separadores decimais (mant\u00e9m apenas o primeiro)
        if ((value.match(/,/g) || []).length > 1) {
            value = value.replace(/,(.*?),/g, '$1'); // Remove v\u00edrgulas extras
        }
        if ((value.match(/\./g) || []).length > 1) {
            value = value.replace(/\.(.*?)\./g, '$1'); // Remove pontos extras
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

    // --- Aplica as restri\u00e7\u00f5es aos campos do formul\u00e1rio de Conta Banc\u00e1ria ---
    // (Estas restri\u00e7\u00f5es ser\u00e3o aplicadas a ambos os templates add.html e edit.html se tiverem os mesmos IDs)

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
