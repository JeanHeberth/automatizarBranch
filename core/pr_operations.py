# core/pr_operations.py
import requests
import webbrowser
from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info
from core.git_operations import get_current_branch

GITHUB_API = "https://api.github.com"


def create_pull_request(repo_path, base="main", title=None, body=""):
    """Cria um Pull Request via GitHub API."""
    token = require_github_token()
    repo = get_repo_info(repo_path)
    head = get_current_branch(repo_path)

    if head == base:
        raise RuntimeError("Você está na branch principal. Crie uma nova branch antes do PR.")

    title = title or f"Merge {head} → {base}"
    url = f"{GITHUB_API}/repos/{repo.owner}/{repo.name}/pulls"
    payload = {"title": title, "head": head, "base": base, "body": body}
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Erro ao criar PR: {response.status_code} {response.text}")

    pr_url = response.json()["html_url"]
    webbrowser.open(pr_url)
    return pr_url


def merge_pull_request(repo_path, pr_number):
    """Faz merge de um PR via API do GitHub."""
    token = require_github_token()
    repo = get_repo_info(repo_path)
    url = f"{GITHUB_API}/repos/{repo.owner}/{repo.name}/pulls/{pr_number}/merge"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    response = requests.put(url, headers=headers, json={"merge_method": "squash"})
    if response.status_code != 200:
        raise RuntimeError(f"Erro ao fazer merge do PR: {response.status_code} {response.text}")
    return response.json()


def list_open_pull_requests(repo_path):
    """Retorna todos os PRs abertos no repositório."""
    token = require_github_token()
    repo = get_repo_info(repo_path)
    url = f"{GITHUB_API}/repos/{repo.owner}/{repo.name}/pulls?state=open"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Erro ao listar PRs: {response.status_code} {response.text}")

    prs = response.json()
    return [f"#{pr['number']} — {pr['title']}" for pr in prs]
