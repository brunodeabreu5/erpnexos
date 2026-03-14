# ERP Paraguay V6

ERP básico em Python com interface desktop (Tkinter) e PostgreSQL.

## Ambiente

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edite `.env` e preencha `DATABASE_URL` com a URL do seu PostgreSQL (usuário, senha, host, porta e nome do banco).
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute a aplicação:
   ```bash
   python main.py
   ```

## Estrutura do projeto

- `main.py` — ponto de entrada da aplicação
- `app/database/` — modelos (SQLAlchemy), engine e inicialização do banco
- `app/services/` — lógica de negócio (autenticação, vendas, dashboard)
- `app/ui/` — interface Tkinter (login e janela principal)
- `app/reports/` — geração de relatórios em PDF

## Build para Windows

Execute `build_windows.bat` para gerar o executável com PyInstaller.

## Login (ambiente de desenvolvimento)

Usuário: `admin`  
Senha: `admin123`

*Credenciais apenas para uso em desenvolvimento.*
