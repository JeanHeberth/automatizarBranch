"""AuthManager: centraliza credenciais em memória para a aplicação.

Não grava em disco; mantém token e usuário apenas na execução atual.
"""
from typing import Optional
from core.logger_config import get_logger

logger = get_logger()


class AuthManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._token = None
            cls._instance._user = None
        return cls._instance

    def set_token(self, token: str):
        self._token = token
        logger.debug("AuthManager: token definido em memória")

    def get_token(self) -> Optional[str]:
        return self._token

    def set_user(self, user: str):
        self._user = user
        logger.debug(f"AuthManager: usuário definido: {user}")

    def get_user(self) -> Optional[str]:
        return self._user

    def clear(self):
        self._token = None
        self._user = None
        logger.debug("AuthManager: credenciais limpas")


# Export singleton
auth_manager = AuthManager()

