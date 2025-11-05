import subprocess
import requests
from pathlib import Path
from typing import List
from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info


class GitCommandError(Exception):
    """Erro personalizado para falhas em comandos Git."""
    pass


def run_git_command(repo_path: str, command_list: List[str]) -> str:
    """Executa comandos Git e retorna a saída limpa."""
    result = subprocess.run(
        ["git", "-C", repo_path] + command_list,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise GitCommandError(result.stderr.strip())
    return result.stdout.strip()


def get_current_branch(repo_path: str) -> str:
    """Retorna o nome da branch atual."""
    return run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])


def rollback_last_commit(repo_path: Path, mode: str = "soft") -> str:
    """Desfaz o último commit."""
    branch = get_current_branch(repo_path)
    if mode == "soft":
        run_git_command(repo_path, ["reset", "--soft", "HEAD~1"])
    elif mode == "hard":
        run_git_command(repo_path, ["fetch", "origin", branch])
        run_git_command(repo_path, ["reset", "--hard", f"origin/{branch}"])
    else:
        raise ValueError("Modo inválido. Use 'soft' ou 'hard'.")
    return branch


def discard_local_changes(repo_path: Path) -> None:
    """Descarta alterações locais não commitadas."""
    try:
        run_git_command(repo_path, ["restore", "."])
    except GitCommandError:
        run_git_command(repo_path, ["checkout", "--", "."])


def merge_pull_request(repo_path: Path, pr_number: int) -> str:
    """Faz o merge de um Pull Request via GitHub API."""
    token = require_github_token()
    if not token:
        raise GitCommandError("GITHUB_TOKEN não encontrado. Adicione no arquivo .env")

    info = get_repo_info(repo_path)
    url = f"https://api.github.com/repos/{info.full_name}/pulls/{pr_number}/merge"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.put(url, headers=headers, json={"merge_method": "squash"})

    if response.status_code == 200:
        return f"✅ PR #{pr_number} mesclado com sucesso!"
    elif response.status_code == 405:
        raise GitCommandError(f"PR #{pr_number} já foi mesclado ou está fechado.")
    else:
        raise GitCommandError(f"Erro ao mesclar PR #{pr_number}: {response.text}")


def get_default_main_branch(repo_path: Path) -> str:
    """
    Detecta automaticamente a branch principal (ex: main, master, develop, etc.).
    Verifica a configuração remota e retorna o nome correto.
    """
    try:
        # 1️⃣ tenta ler a branch padrão definida no remoto
        result = run_git_command(repo_path, ["symbolic-ref", "refs/remotes/origin/HEAD"])
        # Exemplo de saída: "refs/remotes/origin/main"
        return result.split("/")[-1].strip()
    except RuntimeError:
        # 2️⃣ fallback — verifica quais branches existem e escolhe a mais provável
        remotas = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        remotas = [b.strip().replace("origin/", "") for b in remotas if "origin/" in b]

        for name in ["main", "master", "develop", "production"]:
            if name in remotas:
                return name

        # 3️⃣ fallback final — retorna a primeira da lista
        return remotas[0] if remotas else "main"
