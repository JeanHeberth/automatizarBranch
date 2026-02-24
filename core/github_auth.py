"""
Autenticação segura via GitHub CLI (gh) ou Git Credential Manager.
Remove dependência de tokens em .env.
"""
import subprocess
import os
from pathlib import Path
from core.logger_config import get_logger

logger = get_logger()


class GitHubAuthError(Exception):
    """Erro de autenticação GitHub."""
    pass


def get_github_token_from_cli() -> str:
    """
    Obtém token GitHub de forma segura via 'gh' CLI.
    Não armazena token em arquivo!

    Returns:
        Token GitHub autenticado

    Raises:
        GitHubAuthError: Se 'gh' não estiver instalado ou não autenticado
    """
    try:
        # Verificar se 'gh' está instalado e autenticado
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            raise GitHubAuthError(
                "GitHub CLI não autenticado.\n"
                "Execute: gh auth login"
            )

        logger.info("GitHub CLI autenticado com sucesso")

        # Obter token via 'gh'
        token_result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if token_result.returncode != 0:
            raise GitHubAuthError("Erro ao obter token do GitHub CLI")

        token = token_result.stdout.strip()
        logger.debug("Token obtido do GitHub CLI")
        return token

    except FileNotFoundError:
        raise GitHubAuthError(
            "GitHub CLI ('gh') não está instalado.\n"
            "Instale com: brew install gh (macOS)\n"
            "             choco install gh (Windows)\n"
            "             sudo apt-get install gh (Linux)"
        )
    except subprocess.TimeoutExpired:
        raise GitHubAuthError("Timeout ao conectar com GitHub CLI")
    except Exception as e:
        logger.error(f"Erro ao obter token: {e}")
        raise GitHubAuthError(str(e))


def get_github_token() -> str:
    """
    Obtém token GitHub de forma segura.
    Tenta múltiplas fontes:
    1. GitHub CLI (gh) - ⭐ Recomendado
    2. Git Credential Manager - Alternativa
    3. .env (apenas para desenvolvimento local)
    """
    logger.debug("Tentando obter token GitHub de forma segura...")

    # 1️⃣ Tentar GitHub CLI
    try:
        token = get_github_token_from_cli()
        logger.info("✅ Autenticado via GitHub CLI")
        return token
    except GitHubAuthError as e:
        logger.warning(f"GitHub CLI não disponível: {e}")

    # 2️⃣ Tentar Git Credential Manager
    try:
        result = subprocess.run(
            ["git", "credential-manager", "get"],
            input="host=github.com\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse output: password=token
            for line in result.stdout.strip().split('\n'):
                if line.startswith('password='):
                    token = line.replace('password=', '')
                    logger.info("✅ Autenticado via Git Credential Manager")
                    return token
    except Exception as e:
        logger.debug(f"Git Credential Manager não disponível: {e}")

    # 3️⃣ Último recurso: .env (apenas se estiver vazio ou comentado)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("GITHUB_TOKEN")

        if token and not token.startswith("#"):
            logger.warning(
                "⚠️ Usando token de .env (inseguro!)\n"
                "Prefira: gh auth login"
            )
            return token
    except Exception as e:
        logger.debug(f"Erro ao carregar .env: {e}")

    # Nenhum método funcionou
    raise GitHubAuthError(
        "Nenhum método de autenticação disponível!\n\n"
        "Opções:\n"
        "1️⃣ Instale GitHub CLI: brew install gh\n"
        "2️⃣ Autentique: gh auth login\n"
        "3️⃣ Ou use Git Credential Manager\n"
        "4️⃣ Ou defina GITHUB_TOKEN em .env (menos seguro)"
    )


def get_github_user() -> str:
    """Obtém nome de usuário GitHub autenticado."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            username = result.stdout.strip()
            logger.debug(f"Usuário GitHub: {username}")
            return username
        else:
            raise GitHubAuthError("Erro ao obter usuário GitHub")

    except FileNotFoundError:
        raise GitHubAuthError("GitHub CLI não instalado")
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}")
        raise GitHubAuthError(str(e))

