import subprocess
from pathlib import Path



def run_git_command(repo_path, command_list):
    """Executa comandos git e retorna saída limpa."""
    result = subprocess.run(
        ["git", "-C", repo_path] + command_list,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()
# core/git_operations.py  (adicione ao final do arquivo)

def rollback_last_commit(repo_path: Path, mode: str = "soft") -> str:
    branch = get_current_branch(repo_path)
    if mode == "soft":
        run_git_command(repo_path, ["reset", "--soft", "HEAD~1"])
    elif mode == "hard":
        run_git_command(repo_path, ["fetch", "origin", branch])
        run_git_command(repo_path, ["reset", "--hard", f"origin/{branch}"])
    else:
        raise ValueError("Modo inválido. Use 'soft' ou 'hard'.")

    return branch

def get_current_branch(repo_path):
    """Retorna o nome da branch atual."""
    return run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])

class GitCommandError(Exception):
    """Erro personalizado para falhas em comandos Git."""
    pass

