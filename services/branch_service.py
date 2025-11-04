from core.git_operations import run_git_command, get_current_branch, GitCommandError
from typing import List


def list_branches(repo_path: str) -> List[str]:
    """Retorna a lista de branches locais."""
    try:
        raw = run_git_command(repo_path, ["branch"]).splitlines()
        return [b.replace("*", "").strip() for b in raw if b.strip()]
    except Exception as e:
        raise GitCommandError(f"Erro ao listar branches: {e}")


def update_branch(repo_path: str, branch: str) -> str:
    """Atualiza a branch local com o remoto."""
    try:
        run_git_command(repo_path, ["checkout", branch])
        run_git_command(repo_path, ["pull", "origin", branch])
        return f"Branch '{branch}' atualizada com sucesso."
    except Exception as e:
        raise GitCommandError(f"Erro ao atualizar branch: {e}")


def create_branch(repo_path: str, name: str) -> str:
    """Cria uma nova branch local."""
    try:
        run_git_command(repo_path, ["checkout", "-b", name])
        return f"Branch '{name}' criada com sucesso."
    except Exception as e:
        raise GitCommandError(f"Erro ao criar branch: {e}")


def checkout_branch(repo_path: str, name: str) -> str:
    """Realiza checkout para uma branch existente."""
    try:
        run_git_command(repo_path, ["checkout", name])
        return f"Checkout realizado para '{name}'."
    except Exception as e:
        raise GitCommandError(f"Erro ao fazer checkout: {e}")


def list_local_branches(repo_path: str) -> list[str]:
    """Lista as branches locais."""
    raw = run_git_command(repo_path, ["branch"]).splitlines()
    return [b.replace("*", "").strip() for b in raw if b.strip()]


def list_remote_branches(repo_path: str) -> list[str]:
    """Lista as branches remotas."""
    raw = run_git_command(repo_path, ["branch", "-r"]).splitlines()
    return sorted(set(b.strip().replace("origin/", "") for b in raw if "origin/" in b))
