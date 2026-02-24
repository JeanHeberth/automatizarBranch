from typing import List
from core.git_operations import run_git_command, get_current_branch, GitCommandError
from core.logger_config import get_logger
from core.cache import cached

logger = get_logger()


@cached(ttl=5)
def list_branches(repo_path: str) -> List[str]:
    """Lista todas as branches locais do repositório. (Cache: 5s)"""
    try:
        raw = run_git_command(repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in raw if b.strip()]
        logger.debug(f"Branches locais encontradas: {branches}")
        return branches
    except GitCommandError as e:
        logger.error(f"Erro ao listar branches: {e}")
        raise


@cached(ttl=5)
def list_remote_branches(repo_path: str) -> List[str]:
    """Lista todas as branches remotas do repositório. (Cache: 5s)"""
    try:
        raw = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        branches = [b.strip().replace("origin/", "") for b in raw if "origin/" in b]
        branches = sorted(set(branches))
        logger.debug(f"Branches remotas encontradas: {branches}")
        return branches
    except GitCommandError as e:
        logger.error(f"Erro ao listar branches remotas: {e}")
        raise


def update_branch(repo_path: str, branch: str) -> str:
    """Atualiza a branch local com a remota correspondente.
    Se a branch ainda não existir no remoto, realiza o push inicial.
    """
    try:
        logger.info(f"Atualizando branch '{branch}'...")
        # Faz checkout para a branch alvo
        run_git_command(repo_path, ["checkout", branch])

        # Verifica se branch existe no remoto
        remotas = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        remote_exists = any(f"origin/{branch}" in r.strip() for r in remotas)

        if remote_exists:
            run_git_command(repo_path, ["pull", "origin", branch])
            msg = f"✅ Branch '{branch}' atualizada com sucesso."
        else:
            run_git_command(repo_path, ["push", "-u", "origin", branch])
            run_git_command(repo_path, ["pull", "origin", branch])
            msg = f"✅ Branch '{branch}' atualizada com sucesso."

        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao atualizar branch '{branch}': {e}")
        raise GitCommandError(f"Erro ao atualizar branch '{branch}': {e}")


def create_branch(repo_path: str, branch_name: str) -> str:
    """
    Cria uma nova branch.
    Retorna uma mensagem de sucesso.
    """
    try:
        logger.info(f"Criando branch '{branch_name}'...")
        run_git_command(repo_path, ["checkout", "-b", branch_name])
        msg = f"🌱 Branch '{branch_name}' criada com sucesso."
        logger.info(msg)
        return msg
    except GitCommandError as e:
        logger.error(f"Erro ao criar branch '{branch_name}': {e}")
        raise


def checkout_branch(repo_path: str, branch: str) -> str:
    """
    Realiza o checkout para a branch especificada.
    Retorna uma mensagem de sucesso.
    """
    try:
        logger.info(f"Fazendo checkout para '{branch}'...")
        run_git_command(repo_path, ["checkout", branch])
        msg = f"✅ Checkout realizado para '{branch}'."
        logger.info(msg)
        return msg
    except GitCommandError as e:
        logger.error(f"Erro ao fazer checkout para '{branch}': {e}")
        raise


def list_local_branches(repo_path: str) -> List[str]:
    """Retorna as branches locais existentes."""
    try:
        raw = run_git_command(repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in raw if b.strip()]
        logger.debug(f"Branches locais: {branches}")
        return branches
    except GitCommandError as e:
        logger.error(f"Erro ao listar branches locais: {e}")
        raise


def safe_checkout(repo_path, branch):
    """Verifica alterações locais antes de trocar de branch."""
    try:
        logger.info(f"Verificando alterações locais para checkout de '{branch}'...")
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if status.strip():
            msg = (
                "Existem alterações locais não commitadas.\n"
                "Por favor, faça commit, stash ou descarte antes de trocar de branch."
            )
            logger.warning(msg)
            raise GitCommandError(msg)
        run_git_command(repo_path, ["checkout", branch])
        msg = f"Checkout realizado com sucesso para '{branch}'."
        logger.info(msg)
        return msg
    except GitCommandError as e:
        logger.error(f"Erro em safe_checkout: {e}")
        raise
