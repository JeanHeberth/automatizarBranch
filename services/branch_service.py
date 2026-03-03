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


def update_branch(repo_path: str, branch: str, base_branch: str = None, strategy: str = "rebase") -> str:
    """Atualiza a branch local sincronizando com a branch base.

    Fluxo:
    - Faz checkout para `branch`.
    - Faz fetch de `origin/<base_branch>` e `origin/<branch>`.
    - Aplica sincronização conforme `strategy`:
        - "rebase" (padrão): rebase local sobre `origin/<base_branch>` e push com --force-with-lease
        - "merge": merge de `origin/<base_branch>` (preserva merges) e push normal

    Args:
        repo_path: caminho do repositório
        branch: branch local a atualizar
        base_branch: branch base (se None, detecta develop/main/master)
        strategy: "rebase" ou "merge"

    Returns:
        Mensagem de sucesso.

    Raises:
        GitCommandError: em casos de erros git ou conflitos que precisem de ação manual.
    """
    try:
        logger.info(f"Atualizando branch '{branch}' com estratégia '{strategy}'...")

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
                "Faça commit ou descarte antes de atualizar."
            )
            logger.warning(msg)
            raise GitCommandError(msg)

        # Busca informações remotas mais recentes (base e a própria branch)
        logger.debug(f"Fazendo fetch de origin/{base_branch} e origin/{branch}")
        run_git_command(repo_path, ["fetch", "origin", base_branch])
        run_git_command(repo_path, ["fetch", "origin", branch])

        # Verifica se branch existe no remoto usando helper
        remotas = list_remote_branches(repo_path)
        remote_exists = branch in remotas

        if not remote_exists:
            # Branch é nova: push inicial com tracking
            logger.info(f"Branch '{branch}' não existe no remoto. Fazendo push inicial com tracking...")
            run_git_command(repo_path, ["push", "-u", "origin", branch])
            msg = f"✅ Branch '{branch}' criada e enviada ao remoto."
            logger.info(msg)
            return msg

        # Caso exista, sincroniza com a base
        if strategy not in {"rebase", "merge"}:
            raise GitCommandError(f"Strategy inválida: {strategy}. Use 'rebase' ou 'merge'.")

        if strategy == "rebase":
            logger.info(f"Rebaseando '{branch}' sobre origin/{base_branch}...")
            try:
                run_git_command(repo_path, ["rebase", f"origin/{base_branch}"])
            except GitCommandError as e:
                # Tentativa de abortar rebase para deixar repositório em estado limpo
                try:
                    run_git_command(repo_path, ["rebase", "--abort"])
                except Exception:
                    logger.debug("Falha ao abortar rebase automaticamente.")
                msg = (
                    f"⚠️ Conflito durante rebase: {e}.\n"
                    "Resolva os conflitos localmente (git status) e finalize o rebase antes de tentar novamente."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

            # Force push seguro após rebase (preserva trabalho remoto se houver divergência)
            run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])
            msg = f"✅ Branch '{branch}' sincronizada com '{base_branch}' via rebase."

        else:  # merge
            logger.info(f"Mesclando origin/{base_branch} em '{branch}'...")
            try:
                run_git_command(repo_path, ["merge", f"origin/{base_branch}"])
            except GitCommandError as e:
                msg = (
                    f"⚠️ Conflito durante merge: {e}.\n"
                    "Resolva os conflitos localmente e faça commit antes de tentar novamente."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

            # Push normal (merge preserva histórico)
            run_git_command(repo_path, ["push", "origin", branch])
            msg = f"✅ Branch '{branch}' sincronizada com '{base_branch}' via merge."

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
    Cria uma nova branch com prefixo 'feature/'.
    Retorna uma mensagem de sucesso.
    """
    try:
        # Garante prefixo 'feature/'
        if not branch_name.startswith("feature/"):
            branch_name = f"feature/{branch_name}"
        run_git_command(repo_path, ["checkout", "-b", branch_name])
        # Mantém o emoji 🌱 para compatibilidade com testes/UX
        msg = f"🌱 Branch '{branch_name}' criada com sucesso."
        logger.info(msg)
        return msg
    except GitCommandError as e:
        logger.error(f"Erro ao criar branch: {e}")
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


def validate_pr_ready(repo_path: str, base_branch: str, compare_branch: str) -> str:
    """Valida se a branch compare está atualizada e sem conflito com a base."""
    try:
        logger.info(f"Validando PR: '{compare_branch}' -> '{base_branch}'...")

        run_git_command(repo_path, ["fetch", "origin", base_branch])

        try:
            run_git_command(repo_path, ["merge-base", "--is-ancestor", f"origin/{base_branch}", compare_branch])
        except GitCommandError:
            msg = (
                f"⚠️ A branch '{compare_branch}' está desatualizada em relação a '{base_branch}'.\n"
                "Atualize sua branch (rebase/merge) e faça push antes de criar o PR."
            )
            logger.warning(msg)
            raise GitCommandError(msg)

        base_commit = run_git_command(repo_path, ["merge-base", compare_branch, f"origin/{base_branch}"])
        merge_output = run_git_command(repo_path, ["merge-tree", base_commit, compare_branch, f"origin/{base_branch}"])
        if "<<<<<<<" in merge_output or ">>>>>>>" in merge_output:
            msg = (
                f"⚠️ Conflito detectado ao mesclar '{compare_branch}' em '{base_branch}'.\n"
                "Resolva os conflitos localmente e faça push antes de criar o PR."
            )
            logger.warning(msg)
            raise GitCommandError(msg)

        msg = "✅ Branch pronta para criar PR."
        logger.info(msg)
        return msg
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar PR: {e}")
        raise GitCommandError(f"Erro ao validar PR: {e}")


def get_protected_branches() -> List[str]:
    """Retorna lista de branches protegidas (não podem ser deletadas)."""
    return ["main", "master", "develop"]


def delete_all_remote_branches(repo_path: str) -> List[str]:
    """
    Deleta todas as branches remotas não protegidas.
    Retorna lista de branches deletadas.
    """
    try:
        protected = set(get_protected_branches())
        remotas = list_remote_branches(repo_path)
        deletadas = []
        for branch in remotas:
            if branch not in protected:
                try:
                    run_git_command(repo_path, ["push", "origin", f":{branch}"])
                    deletadas.append(branch)
                    logger.info(f"Branch remota '{branch}' deletada.")
                except GitCommandError as e:
                    logger.warning(f"Erro ao deletar branch remota '{branch}': {e}")
        return deletadas
    except Exception as e:
        logger.error(f"Erro ao deletar branches remotas: {e}")
        raise GitCommandError(f"Erro ao deletar branches remotas: {e}")
