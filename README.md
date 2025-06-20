Estrutura do projeto: Finanças WEB

financas_web
├── venv/
├── .env
├── .gitignore
├── config.py
├── README.md
├── requirements.txt
├── run.py								
│
├── database/
│   ├── __init__.py
│   └── db_manager.py
│
├── models/
│   ├── conta_bancaria_model.py
│   ├── crediario_model.py
│   ├── despesa_fixa_model.py
│   ├── despesa_receita_model.py
│   ├── grupo_crediario_model.py
│   ├── movimento_bancario_model.py
│   ├── movimento_crediario_model.py
│   ├── movimento_renda_model.py        ***NOVO
│   ├── parcela_crediario_model.py
│   ├── renda_model.py
│   ├── transacao_bancaria_model.py
│   └── usuario_model.py
│
├── routes/
│   ├── conta_bancaria_routes.py
│   ├── crediario_routes.py
│   ├── despesa_fixa_routes.py
│   ├── despesa_receita_routes.py
│   ├── extratos_bancario_routes.py
│   ├── extratos_crediario_routes.py
│   ├── grupo_crediario_routes.py
│   ├── movimento_bancario_routes.py
│   ├── movimento_crediario_routes.py
│   ├── movimento_renda_routes.py   ***NOVO
│   ├── renda_routes.py
│   ├── transacao_bancaria_routes.py
│   └── usuario_routes.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── img/
│       ├── logo.png
│       └── icone.png
│
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── includes/
    │   ├── _navbar.html				
    │   └── _footer.html
    ├── errors/
    │   ├── 404.html
    │   └── 500.html
    ├── conta_bancaria/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── crediario/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── despesa_fixa/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── despesa_receita/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── extratos/
    │   ├── bancario_form.html
    │   ├── bancario_view.html
    │   ├── crediario_form.html
    │   ├── crediario_view.html
    │   └── parcelas_view.html
    ├── grupo_crediario/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── movimento_bancario/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── movimento_crediario/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── movimento_renda/    ***NOVO
    │   ├── add.html        ***NOVO
    │   ├── edit.html       ***NOVO
    │   └── list.html       ***NOVO
    ├── renda/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── transacao_bancaria/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html
    ├── usuario/
    │   ├── add.html
    │   ├── edit.html
    │   └── list.html 

