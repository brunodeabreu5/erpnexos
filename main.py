
from app.config import setup_logging, validate_configuration
from app.database.init_db import init_db
from app.ui.main_window import run_app

if __name__ == "__main__":
    # Setup logging first
    setup_logging()

    # Validate configuration before starting
    if not validate_configuration():
        raise SystemExit(
            "Falha na validação de configuração. "
            "Por favor, verifique as mensagens de erro acima e corrija as configurações no arquivo .env"
        )

    # Initialize database
    if not init_db():
        raise SystemExit("Falha ao inicializar o banco. Verifique o .env e se o PostgreSQL está rodando.")

    # Run application
    run_app()
