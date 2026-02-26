from core.git_operations import run_git_command, get_current_branch, GitCommandError
from core.logger_config import get_logger

logger = get_logger()


def commit_changes(repo_path: str, message: str) -> str:
    """Realiza apenas o commit."""
    try:
        logger.info(f"Realizando commit com mensagem: '{message}'...")
        run_git_command(repo_path, ["add", "."])
        run_git_command(repo_path, ["commit", "-m", message])
        msg = f"Commit realizado: {message}"
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao fazer commit: {e}")
        raise GitCommandError(f"Erro no commit: {e}")


def commit_and_push(repo_path: str, message: str) -> str:
    """Realiza commit e push.

    Nota: Se a branch foi feita rebase recentemente, usa --force-with-lease
    para push seguro.
    """
    try:
        logger.info(f"Realizando commit + push com mensagem: '{message}'...")
        branch = get_current_branch(repo_path)
        run_git_command(repo_path, ["add", "."])
        run_git_command(repo_path, ["commit", "-m", message])

        # Tentar push normal primeiro
        try:
            run_git_command(repo_path, ["push", "origin", branch])
        except GitCommandError:
            # Se falhar, tentar com force-with-lease (seguro após rebase)
            logger.info("Push falhou. Tentando com --force-with-lease...")
            run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])

        msg = f"Commit e push enviados para 'origin/{branch}'."
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao fazer commit/push: {e}")
        raise GitCommandError(f"Erro ao enviar commit/push: {e}")
