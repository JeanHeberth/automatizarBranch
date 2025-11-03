# core/git_operations.py
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from utils.repo_utils import get_repo_info, RepoInfo
from core.env_utils import get_github_token

class GitCommandError(Exception):
    """Erro genérico ao executar comandos Git."""
    pass

# ------------------------------------------------------------
# 🔹 Funções auxiliares
# ------------------------------------------------------------

def run_git_command(repo_path: Path, args: list[str]) -> str:
    """
    Executa um comando git e retorna o stdout (limpo).
    Lança exceção se o comando falhar.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitCommandError(
            f"Erro ao executar git {' '.join(args)}: {e.stderr.strip()}"
        )

# ------------------------------------------------------------
# 🔹 Funções principais da automação
# ------------------------------------------------------------

def get_current_branch(repo_path: Path) -> str:
    """
    Retorna o nome da branch atual.
    """
    return run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])

def create_branch(repo_path: Path, branch_name: str, base: str = "main") -> str:
    """
    Cria uma nova branch a partir da base (por padrão, main).
    """
    run_git_command(repo_path, ["checkout", base])
    run_git_command(repo_path, ["pull", "origin", base])
    run_git_command(repo_path, ["checkout", "-b", branch_name])
    return branch_name

def commit_and_push(repo_path: Path, message: str) -> Tuple[str, str]:
    """
    Adiciona alterações, faz commit e push da branch atual.
    Retorna (branch_name, remote_url)
    """
    run_git_command(repo_path, ["add", "."])
    run_git_command(repo_path, ["commit", "-m", message])
    branch = get_current_branch(repo_path)
    run_git_command(repo_path, ["push", "-u", "origin", branch])

    repo_info = get_repo_info(repo_path)
    remote_url = f"https://{repo_info.host}/{repo_info.full_name}"
    return branch, remote_url

def merge_to_main(repo_path: Path) -> None:
    """
    Faz merge da branch atual na main (local).
    """
    current = get_current_branch(repo_path)
    if current == "main":
        print("[INFO] Já está na branch main.")
        return
    run_git_command(repo_path, ["checkout", "main"])
    run_git_command(repo_path, ["pull", "origin", "main"])
    run_git_command(repo_path, ["merge", current])
    run_git_command(repo_path, ["push", "origin", "main"])
    print(f"[OK] Merge concluído de {current} → main")

def get_repo_info_summary(repo_path: Path) -> str:
    """
    Retorna uma string amigável com dados do repositório.
    """
    info = get_repo_info(repo_path)
    return f"{info.full_name} ({info.host})"

def get_authenticated_repo_url(repo_path: Path) -> str:
    """
    Retorna a URL do repositório, incluindo token se existir (para operações via API).
    Exemplo:
        https://<token>@github.com/user/repo.git
    """
    token = get_github_token()
    info = get_repo_info(repo_path)

    if token:
        return f"https://{token}@{info.host}/{info.full_name}.git"
    return f"https://{info.host}/{info.full_name}.git"
