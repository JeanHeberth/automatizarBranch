from typing import List
from core.git_operations import run_git_command, GitCommandError
from core.logger_config import get_logger

logger = get_logger()


def stash_save(repo_path: str, message: str = None) -> str:
    """
    Salva as alterações locais em um stash.

    Args:
        repo_path: Caminho do repositório
        message: Mensagem descritiva opcional para o stash

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info(f"Salvando alterações em stash...")

        # Verificar se há alterações para salvar
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if not status.strip():
            msg = "Não há alterações para salvar no stash."
            logger.info(msg)
            return msg

        # Salvar stash com ou sem mensagem
        if message:
            run_git_command(repo_path, ["stash", "save", message])
            msg = f"💾 Stash salvo: '{message}'"
        else:
            run_git_command(repo_path, ["stash"])
            msg = "💾 Stash salvo com sucesso."

        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao salvar stash: {e}")
        raise GitCommandError(f"Erro ao salvar stash: {e}")


def stash_list(repo_path: str) -> List[str]:
    """
    Lista todos os stashes salvos.

    Returns:
        Lista de stashes no formato: "stash@{0}: mensagem"
    """
    try:
        logger.info("Listando stashes...")
        result = run_git_command(repo_path, ["stash", "list"])

        if not result.strip():
            logger.info("Nenhum stash encontrado.")
            return []

        stashes = result.strip().split("\n")
        logger.info(f"Encontrados {len(stashes)} stash(es).")
        return stashes
    except Exception as e:
        logger.error(f"Erro ao listar stashes: {e}")
        raise GitCommandError(f"Erro ao listar stashes: {e}")


def stash_apply(repo_path: str, stash_ref: str = "stash@{0}") -> str:
    """
    Aplica um stash sem removê-lo da lista.

    Args:
        repo_path: Caminho do repositório
        stash_ref: Referência do stash (padrão: stash@{0} - o mais recente)

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info(f"Aplicando stash: {stash_ref}...")
        run_git_command(repo_path, ["stash", "apply", stash_ref])
        msg = f"✅ Stash '{stash_ref}' aplicado com sucesso."
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao aplicar stash: {e}")
        raise GitCommandError(f"Erro ao aplicar stash '{stash_ref}': {e}")


def stash_pop(repo_path: str, stash_ref: str = "stash@{0}") -> str:
    """
    Aplica um stash e o remove da lista.

    Args:
        repo_path: Caminho do repositório
        stash_ref: Referência do stash (padrão: stash@{0} - o mais recente)

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info(f"Aplicando e removendo stash: {stash_ref}...")
        run_git_command(repo_path, ["stash", "pop", stash_ref])
        msg = f"✅ Stash '{stash_ref}' aplicado e removido com sucesso."
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao aplicar/remover stash: {e}")
        raise GitCommandError(f"Erro ao aplicar/remover stash '{stash_ref}': {e}")


def stash_drop(repo_path: str, stash_ref: str = "stash@{0}") -> str:
    """
    Remove um stash específico sem aplicá-lo.

    Args:
        repo_path: Caminho do repositório
        stash_ref: Referência do stash (padrão: stash@{0} - o mais recente)

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info(f"Removendo stash: {stash_ref}...")
        run_git_command(repo_path, ["stash", "drop", stash_ref])
        msg = f"🗑️ Stash '{stash_ref}' removido com sucesso."
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao remover stash: {e}")
        raise GitCommandError(f"Erro ao remover stash '{stash_ref}': {e}")


def stash_clear(repo_path: str) -> str:
    """
    Remove todos os stashes salvos.

    Returns:
        Mensagem de sucesso
    """
    try:
        logger.info("Removendo todos os stashes...")

        # Verificar se há stashes antes de limpar
        stashes = stash_list(repo_path)
        if not stashes:
            msg = "Não há stashes para remover."
            logger.info(msg)
            return msg

        run_git_command(repo_path, ["stash", "clear"])
        msg = f"🧹 Todos os stashes ({len(stashes)}) foram removidos com sucesso."
        logger.info(msg)
        return msg
    except Exception as e:
        logger.error(f"Erro ao limpar stashes: {e}")
        raise GitCommandError(f"Erro ao limpar stashes: {e}")


def stash_show(repo_path: str, stash_ref: str = "stash@{0}") -> str:
    """
    Mostra o conteúdo de um stash específico.

    Args:
        repo_path: Caminho do repositório
        stash_ref: Referência do stash (padrão: stash@{0} - o mais recente)

    Returns:
        Conteúdo do stash
    """
    try:
        logger.info(f"Mostrando conteúdo do stash: {stash_ref}...")
        result = run_git_command(repo_path, ["stash", "show", "-p", stash_ref])
        return result
    except Exception as e:
        logger.error(f"Erro ao mostrar stash: {e}")
        raise GitCommandError(f"Erro ao mostrar stash '{stash_ref}': {e}")

