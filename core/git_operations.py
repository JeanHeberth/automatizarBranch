import subprocess
from pathlib import Path
import requests
from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info


class GitCommandError(Exception):
    """Erro personalizado para falhas em comandos Git."""
    pass


def run_git_command(repo_path, command_list):
    """Executa um comando Git genérico e retorna a saída limpa."""
    result = subprocess.run(
        ["git", "-C", repo_path] + command_list,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise GitCommandError(result.stderr.strip())
    return result.stdout.strip()


def get_current_branch(repo_path: Path) -> str:
    """Retorna o nome da branch atual."""
    return run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])


def rollback_last_commit(repo_path: Path, mode: str = "soft") -> str:
    """
    Desfaz o último commit.
    mode:
      - 'soft': mantém alterações no diretório (git reset --soft HEAD~1)
      - 'hard': reverte completamente ao estado remoto (git reset --hard origin/<branch>)
    """
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
    """Descarta todas as alterações locais não commitadas."""
    try:
        run_git_command(repo_path, ["restore", "."])
    except GitCommandError:
        # Compatibilidade com versões antigas do Git
        run_git_command(repo_path, ["checkout", "--", "."])


def merge_pull_request(repo_path: Path, pr_number: int) -> str:
    """
    Faz o merge de um Pull Request via GitHub API.
    Requer um token válido no .env (GITHUB_TOKEN=...).
    """
    token = require_github_token()
    if not token:
        raise GitCommandError("❌ GITHUB_TOKEN não encontrado. Adicione no arquivo .env")

    info = get_repo_info(repo_path)
    url = f"https://api.github.com/repos/{info.full_name}/pulls/{pr_number}/merge"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.put(url, headers=headers, json={"merge_method": "squash"})

    if response.status_code == 200:
        return f"✅ Pull Request #{pr_number} mesclado com sucesso!"
    elif response.status_code == 405:
        raise GitCommandError(f"⚠️ PR #{pr_number} já foi mesclado ou está fechado.")
    else:
        raise GitCommandError(f"❌ Erro ao mesclar PR #{pr_number}: {response.text}")
