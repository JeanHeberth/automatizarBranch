# core/env_utils.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class EnvInfo:
    """
    Representa as variáveis de ambiente relevantes da automação.
    """
    github_token: Optional[str] = None

def load_environment(env_path: str | Path = ".env") -> EnvInfo:
    """
    Carrega variáveis do arquivo .env (se existir) e do ambiente atual.
    Retorna um objeto EnvInfo com o token do GitHub, se disponível.
    """
    env_path = Path(env_path).expanduser().resolve()
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Não é erro crítico — apenas registra ausência de .env
        print(f"[INFO] Nenhum arquivo .env encontrado em {env_path}. Usando variáveis do ambiente.")

    token = os.getenv("GITHUB_TOKEN")

    return EnvInfo(
        github_token=token.strip() if token else None
    )

def get_github_token() -> Optional[str]:
    """
    Retorna o token do GitHub se disponível.
    """
    env = load_environment()
    return env.github_token

def require_github_token() -> str:
    """
    Retorna o token do GitHub ou lança uma exceção caso não exista.
    Ideal para funções críticas (ex: criação de PRs via API).
    """
    token = get_github_token()
    if not token:
        raise RuntimeError(
            "Nenhum token do GitHub encontrado. "
            "Crie um arquivo .env com a linha:\n"
            "GITHUB_TOKEN=seu_token_aqui\n"
            "ou defina a variável de ambiente GITHUB_TOKEN."
        )
    return token
