from dotenv import load_dotenv
import os


def require_github_token() -> str:
    """Lê o token do GitHub a partir do .env."""
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("Token do GitHub não encontrado. Crie um arquivo .env com GITHUB_TOKEN=...")
    return token
