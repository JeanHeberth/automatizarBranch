from typing import List
from core.git_operations import run_git_command, get_current_branch, GitCommandError


def list_branches(repo_path: str) -> List[str]:
    """Lista todas as branches locais do repositório."""
    raw = run_git_command(repo_path, ["branch"]).splitlines()
    return [b.replace("*", "").strip() for b in raw if b.strip()]


def list_remote_branches(repo_path: str) -> List[str]:
    """Lista todas as branches remotas do repositório."""
    raw = run_git_command(repo_path, ["branch", "-r"]).splitlines()
    branches = [b.strip().replace("origin/", "") for b in raw if "origin/" in b]
    return sorted(set(branches))


def update_branch(repo_path: str, branch: str) -> None:
    """Atualiza a branch local com a remota correspondente."""
    run_git_command(repo_path, ["checkout", branch])
    run_git_command(repo_path, ["pull", "origin", branch])


def create_branch(repo_path: str, branch_name: str) -> None:
    """Cria uma nova branch."""
    run_git_command(repo_path, ["checkout", "-b", branch_name])


def checkout_branch(repo_path: str, branch: str) -> None:
    """Realiza o checkout para a branch especificada."""
    run_git_command(repo_path, ["checkout", branch])


def list_local_branches(repo_path: str) -> List[str]:
    """Retorna as branches locais existentes."""
    raw = run_git_command(repo_path, ["branch"]).splitlines()
    return [b.replace("*", "").strip() for b in raw if b.strip()]
