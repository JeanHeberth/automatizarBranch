"""
Sistema de logging centralizado para o projeto.
Mantém logs tanto em arquivo quanto em memória para UI.
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


class UILogHandler(logging.Handler):
    """Handler customizado para capturar logs e enviar para UI."""

    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        """Emite log formatado para lista interna."""
        msg = self.format(record)
        self.logs.append(msg)

    def get_logs(self):
        """Retorna logs capturados."""
        return self.logs

    def clear_logs(self):
        """Limpa logs em memória."""
        self.logs.clear()


def setup_logging() -> logging.Logger:
    """Configura logging com arquivo rotativo + handler para UI."""

    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Criar logger principal
    logger = logging.getLogger("git_automation")
    logger.setLevel(logging.DEBUG)

    # Handler para arquivo com rotação (máx 5 arquivos de 1MB)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "git_automation.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para UI
    ui_handler = UILogHandler()
    ui_handler.setLevel(logging.INFO)

    # Formato detalhado
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s - %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    ui_handler.setFormatter(formatter)

    # Adicionar handlers
    logger.addHandler(file_handler)
    logger.addHandler(ui_handler)

    return logger


def get_logger() -> logging.Logger:
    """Retorna logger já configurado."""
    return logging.getLogger("git_automation")


def get_ui_handler() -> UILogHandler:
    """Retorna handler de UI para capturar logs."""
    logger = logging.getLogger("git_automation")
    for handler in logger.handlers:
        if isinstance(handler, UILogHandler):
            return handler
    return None

