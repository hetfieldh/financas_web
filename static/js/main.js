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

    // Você pode adicionar mais scripts aqui, por exemplo:
    // - Validações de formulário complexas
    // - Animações
    // - Requisições AJAX (se necessário para interações dinâmicas sem recarregar a página)
    // - Componentes interativos, etc.
});
