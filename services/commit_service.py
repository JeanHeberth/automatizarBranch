from core.git_operations import run_git_command, get_current_branch, GitCommandError


def commit_changes(repo_path: str, message: str) -> str:
    """Realiza apenas o commit."""
    try:
        run_git_command(repo_path, ["add", "."])
        run_git_command(repo_path, ["commit", "-m", message])
        return f"Commit realizado: {message}"
    except Exception as e:
        raise GitCommandError(f"Erro no commit: {e}")


def commit_and_push(repo_path: str, message: str) -> str:
    """Realiza commit e push."""
    try:
        branch = get_current_branch(repo_path)
        run_git_command(repo_path, ["add", "."])
        run_git_command(repo_path, ["commit", "-m", message])
        run_git_command(repo_path, ["push", "-u", "origin", branch])
        return f"Commit e push enviados para 'origin/{branch}'."
    except Exception as e:
        raise GitCommandError(f"Erro ao enviar commit/push: {e}")
