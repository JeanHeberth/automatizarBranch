from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info
import requests
from pathlib import Path


def create_pull_request(repo_path: Path, base: str, title: str) -> str:
    """Cria um Pull Request via API do GitHub."""
    token = require_github_token()
    info = get_repo_info(repo_path)
    url = f"https://api.github.com/repos/{info.full_name}/pulls"

    data = {"title": title, "head": base, "base": "main"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code in (200, 201):
        return response.json().get("html_url", "PR criado com sucesso.")
    else:
        raise Exception(f"Erro ao criar PR: {response.status_code} - {response.text}")
