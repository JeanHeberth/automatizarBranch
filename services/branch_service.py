from typing import List
from core.git_operations import run_git_command, GitCommandError
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


def update_branch(repo_path: str, branch: str, base_branch: str = None) -> str:
    """Atualiza a branch local com a remota e sincroniza com a branch base.

    Evita conflitos em PR/MR ao fazer rebase com a branch base (develop/main).

    Args:
        repo_path: Caminho do repositório
        branch: Nome da branch a atualizar
        base_branch: Branch base para sincronização (padrão: develop ou main)

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info(f"Atualizando branch '{branch}'...")

        # Faz checkout para a branch alvo
        run_git_command(repo_path, ["checkout", branch])

        # Detectar branch base padrão se não informada
        if not base_branch:
            base_branch = _get_default_base_branch(repo_path)

        # Verifica alterações locais não commitadas
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if status.strip():
            msg = (
                f"⚠️ Existem alterações locais em '{branch}'.\n"
                "Commit ou descarte antes de atualizar."
            )
            logger.warning(msg)
            raise GitCommandError(msg)

        # Verifica se branch existe no remoto
        remotas = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        remote_exists = any(f"origin/{branch}" in r.strip() for r in remotas)

        if remote_exists:
            # Branch já existe no remoto: fazer fetch e rebase
            logger.info(f"Sincronizando com 'origin/{base_branch}'...")
            run_git_command(repo_path, ["fetch", "origin", base_branch])
            run_git_command(repo_path, ["rebase", f"origin/{base_branch}"])

            # Force push seguro após rebase
            run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])
            msg = f"✅ Branch '{branch}' sincronizada com '{base_branch}'."
        else:
            # Branch é nova: fazer push inicial com tracking
            logger.info(f"Criando tracking para 'origin/{branch}'...")
            run_git_command(repo_path, ["push", "-u", "origin", branch])
            msg = f"✅ Branch '{branch}' criada e enviada ao remoto."

        logger.info(msg)
        return msg
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar branch '{branch}': {e}")
        raise GitCommandError(f"Erro ao atualizar branch '{branch}': {e}")


def _get_default_base_branch(repo_path: str) -> str:
    """Detecta a branch base padrão (develop ou main)."""
    try:
        # Tentar branches comuns
        for branch_name in ["develop", "main", "master"]:
            try:
                run_git_command(repo_path, ["rev-parse", "--verify", f"origin/{branch_name}"])
                logger.debug(f"Branch base detectada: {branch_name}")
                return branch_name
            except GitCommandError:
                continue

        # Fallback para 'main' se nenhuma for encontrada
        logger.warning("Nenhuma branch base padrão encontrada. Usando 'main'.")
        return "main"
    except Exception as e:
        logger.warning(f"Erro ao detectar branch base: {e}. Usando 'main'.")
        return "main"


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
    """Retorna as branches locais existentes. (Alias para list_branches)"""
    return list_branches(repo_path)


def safe_checkout(repo_path, branch):
    """Verifica alterações locais antes de trocar de branch."""
    try:
        logger.info(f"Verificando alterações locais para checkout de '{branch}'...")
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if status.strip():
            msg = (
                "⚠️ Existem alterações locais não commitadas.\n\n"
                "Você pode:\n"
                "1. 💾 Salvar em Stash (recomendado)\n"
                "2. 💬 Fazer Commit\n"
                "3. ↩️ Descartar alterações\n\n"
                "Use a função 'Stash' para salvar seu trabalho temporariamente."
            )
            logger.warning(msg)
            raise GitCommandError(msg)
        run_git_command(repo_path, ["checkout", branch])
        msg = f"✅ Checkout realizado com sucesso para '{branch}'."
        logger.info(msg)
        return msg
    except GitCommandError as e:
        logger.error(f"Erro em safe_checkout: {e}")
        raise
