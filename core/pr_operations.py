import requests
from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info
from core.git_operations import GitCommandError


def create_pull_request(repo_path: str, base_branch: str, title: str) -> str:
    """
    Cria um Pull Request no GitHub.
    A branch "compare" é a atual (retirada via repo_utils).
    """
    token = require_github_token()
    if not token:
        raise GitCommandError("❌ GITHUB_TOKEN não encontrado. Adicione no arquivo .env")

    info = get_repo_info(repo_path)
    url = f"https://api.github.com/repos/{info.full_name}/pulls"

    payload = {
        "title": title,
        "head": info.current_branch,
        "base": base_branch,
        "body": f"Pull Request automatizado via Tkinter Git App."
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json().get("html_url", "✅ Pull Request criado com sucesso!")
    else:
        raise GitCommandError(f"❌ Erro ao criar PR: {response.text}")
