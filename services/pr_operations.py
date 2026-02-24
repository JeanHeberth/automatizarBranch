"""
Operações de Pull Request via GitHub API.
Autenticação segura via GitHub CLI (gh) ou Git Credential Manager.
"""
import requests
from pathlib import Path
from core.logger_config import get_logger
from utils.repo_utils import get_repo_info
from core.github_auth import get_github_token, GitHubAuthError

logger = get_logger()


def create_pull_request(repo_path: Path, base: str, compare: str, title: str) -> str:
    """
    Cria um Pull Request no GitHub via API.

    Autenticação:
    - ⭐ GitHub CLI (gh auth login) - Recomendado
    - Git Credential Manager - Alternativa
    - .env GITHUB_TOKEN - Apenas desenvolvimento local

    Args:
        repo_path: Caminho do repositório
        base: Branch de destino (ex: main)
        compare: Branch de origem (ex: feature/nova-funcao)
        title: Título do PR

    Returns:
        URL do PR criado

    Raises:
        GitHubAuthError: Se falhar autenticação
        Exception: Se falhar criação do PR
    """
    try:
        logger.info(f"Criando PR: {compare} → {base}")

        # ✨ Obter token de forma segura
        try:
            token = get_github_token()
        except GitHubAuthError as e:
            logger.error(f"Erro de autenticação: {e}")
            raise Exception(str(e))

        info = get_repo_info(repo_path)
        url = f"https://api.github.com/repos/{info.full_name}/pulls"

        data = {"title": title, "head": compare, "base": base}
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code in (200, 201):
            pr_url = response.json().get("html_url", "")
            pr_number = response.json().get("number", "?")
            msg = f"✅ Pull Request #{pr_number} criado com sucesso!\n{pr_url}"
            logger.info(msg)
            return msg
        else:
            error_msg = f"Erro ao criar PR: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except GitHubAuthError as e:
        logger.error(f"Falha de autenticação: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao criar PR: {e}")
        raise

