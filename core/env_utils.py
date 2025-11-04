import os
from dotenv import load_dotenv

load_dotenv()

def require_github_token():
    """Obtém token do GitHub do ambiente."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Token do GitHub não encontrado. Defina GITHUB_TOKEN no .env.")
    return token
