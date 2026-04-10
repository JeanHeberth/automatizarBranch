from typing import List
from core.git_operations import run_git_command, GitCommandError
from core.logger_config import get_logger
from core.cache import cached
from utils.settings import get_protected_branches as _get_protected_branches, get_default_strategy
import json
import shutil
import tempfile
import subprocess

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


def update_branch(repo_path: str, branch: str, base_branch: str = None, strategy: str = None) -> str:
    """Atualiza a branch local sincronizando com a branch base.

    Fluxo:
    - Faz checkout para `branch`.
    - Para `main`/`master`: faz um pull --ff-only de origin/<branch> para garantir que a branch local acompanhe o
      último merge remoto (como no padrão do IntelliJ que reflete o último PR mesclado).
    - Para demais branches: comporta-se conforme estratégia (rebase/merge) como antes.
    """
    try:
        logger.info(f"Atualizando branch '{branch}' com estratgia '{strategy}'...")

        # Faz checkout para a branch alvo
        run_git_command(repo_path, ["checkout", branch])

        # Verifica alteracoes locais no commitadas (apos checkout)
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if status.strip():
            msg = (
                f"⚠️ Existem alteraes locais em '{branch}'.\n"
                "Faa commit ou descarte antes de atualizar."
            )
            logger.warning(msg)
            raise GitCommandError(msg)

        # Caso especial: atualizar branch principal (main/master) para refletir o ultimo PR mesclado
        if branch in {"main", "master"}:
            logger.info(f"Atualizando branch principal '{branch}' para o ultimo merge remoto (origin/{branch})...")
            # Buscar o estado remoto
            run_git_command(repo_path, ["fetch", "origin", branch])

            remotas = list_remote_branches(repo_path)
            remote_exists = branch in remotas

            if not remote_exists:
                # Se nao existe no remoto, push inicial com tracking
                logger.info(f"Branch principal '{branch}' nao existe no remoto. Fazendo push inicial com tracking...")
                run_git_command(repo_path, ["push", "-u", "origin", branch])
                msg = f"✅ Branch '{branch}' criada e enviada ao remoto."
                logger.info(msg)
                return msg

            # Tentar fast-forward pull (sem mesclar) — reflete o ultimo PR mesclado no remoto
            try:
                run_git_command(repo_path, ["pull", "--ff-only", "origin", branch])
            except GitCommandError as e:
                msg = (
                    f"⚠️ Nao foi possivel atualizar '{branch}' via fast-forward: {e}.\n"
                    "Pode haver divergencia entre o local e origin. Faça commit/backup e execute 'git fetch origin && git reset --hard origin/" + branch + "' se desejar forcar."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

            msg = "Atualizado com sucesso!"
            logger.info(msg)
            return msg

        # Para outras branches, detecta branch base padrao se nao informada
        if not base_branch:
            base_branch = _get_default_base_branch(repo_path)

        # Se a base detectada for a própria branch (ex: atualizar 'develop' com base 'develop'),
        # apenas atualize a branch a partir do remoto (pull) em vez de tentar rebase/merge sobre si mesma.
        if base_branch == branch:
            logger.info(f"Base igual à branch ('{branch}'). Fazendo pull de origin/{branch} para atualizar.")
            # Buscar remoto e dar pull normal (não forçamos rebase aqui)
            run_git_command(repo_path, ["fetch", "origin", branch])
            try:
                run_git_command(repo_path, ["pull", "origin", branch])
            except GitCommandError as e:
                # Se houver conflito ou outras situações, repassar erro com instruções
                msg = (
                    f"⚠️ Falha ao atualizar '{branch}' a partir de origin/{branch}: {e}.\n"
                    "Verifique alterações locais ou use a função de forçar sincronização se desejar sobrescrever o local."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

            msg = "Atualizado com sucesso!"
            logger.info(msg)
            return msg

        # Buscar estrategia padrao do usuario se nao fornecida
        if not strategy:
            strategy = get_default_strategy()

        # Buscar informacoes remotas mais recentes (base e a propria branch)
        logger.debug(f"Fazendo fetch de origin/{base_branch} e origin/{branch}")
        run_git_command(repo_path, ["fetch", "origin", base_branch])
        run_git_command(repo_path, ["fetch", "origin", branch])

        # Verifica se branch existe no remoto
        remotas = list_remote_branches(repo_path)
        remote_exists = branch in remotas

        if not remote_exists:
            # Branch nova: push inicial com tracking
            logger.info(f"Branch '{branch}' nao existe no remoto. Fazendo push inicial com tracking...")
            run_git_command(repo_path, ["push", "-u", "origin", branch])
            msg = f"✅ Branch '{branch}' criada e enviada ao remoto."
            logger.info(msg)
            return msg

        # Caso exista, sincroniza com a base conforme estrategia
        if strategy not in {"rebase", "merge"}:
            raise GitCommandError(f"Strategy invalida: {strategy}. Use 'rebase' ou 'merge'.")

        if strategy == "rebase":
            logger.info(f"Rebaseando '{branch}' sobre origin/{base_branch}...")
            try:
                run_git_command(repo_path, ["rebase", f"origin/{base_branch}"])
            except GitCommandError as e:
                # Tentativa de abortar rebase para deixar repositorio em estado limpo
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

            # Force push seguro apos rebase
            run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])
            msg = f"✅ Branch '{branch}' sincronizada com '{base_branch}' via rebase."

        else:  # merge
            logger.info(f"Mesclando origin/{base_branch} em '{branch}'...")
            try:
                run_git_command(repo_path, ["merge", f"origin/{base_branch}"])
            except GitCommandError as e:
                msg = (
                    f"⚠️ Conflito durante merge: {e}.\n"
                    "Resolva os conflitos localmente e faca commit antes de tentar novamente."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

            # Push normal (merge preserva historico)
            run_git_command(repo_path, ["push", "origin", branch])
            msg = f"✅ Branch '{branch}' sincronizada com '{base_branch}' via merge."

        logger.info(msg)
        return msg
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar branch '{branch}': {e}")
        raise GitCommandError(f"Erro ao atualizar branch '{branch}': {e}")


def force_sync_branch(repo_path: str, branch: str, stash_backup: bool = False) -> str:
    """Força sincronização da branch local com origin/<branch> usando reset --hard.

    Se `stash_backup` for True, as alterações locais não commitadas serão salvas em stash antes do reset.
    Retorna mensagem de sucesso.
    """
    try:
        logger.info(f"Forçando sincronização de '{branch}' (stash_backup={stash_backup})...")

        # Fazer fetch do remoto
        run_git_command(repo_path, ["fetch", "origin", branch])

        # Verificar alterações locais
        status = run_git_command(repo_path, ["status", "--porcelain"])
        if status.strip():
            if stash_backup:
                logger.info("Alterações locais detectadas — criando stash de backup antes do reset")
                stash_msg = run_git_command(repo_path, ["stash", "push", "-m", "backup before force sync"]) or "stash created"
                logger.debug(f"Stash criado: {stash_msg}")
            else:
                msg = (
                    "⚠️ Existem alterações locais não commitadas. Use 'stash_backup=True' para salvar antes de forçar,"
                    " ou faça commit/discard manualmente."
                )
                logger.warning(msg)
                raise GitCommandError(msg)

        # Reset hard para origin/<branch>
        run_git_command(repo_path, ["reset", "--hard", f"origin/{branch}"])

        msg = "Atualizado com sucesso!"
        logger.info(msg)
        return msg
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro ao forçar sincronização: {e}")
        raise GitCommandError(str(e))


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


def create_branch(repo_path: str, branch_name: str, base_branch: str | None = None) -> str:
    """
    Cria uma nova branch com prefixo 'feature/'.
    Retorna uma mensagem de sucesso.
    """
    try:
        # Garante prefixo 'feature/'
        if not branch_name.startswith("feature/"):
            branch_name = f"feature/{branch_name}"

        # Atualizar remotos primeiro para garantir que list_remote_branches retorne dados recentes
        try:
            run_git_command(repo_path, ["fetch", "origin"])
        except GitCommandError:
            logger.debug("Falha ao executar 'git fetch origin' antes de criar branch; prosseguindo com detecção local/remota existente.")

        # Se o usuário passou explicitamente a base, utilize-a; senão prefira main/master
        if not base_branch:
            try:
                remotas = list_remote_branches(repo_path)
            except Exception:
                remotas = []

            if "main" in remotas:
                base_branch = "main"
            elif "master" in remotas:
                base_branch = "master"
            else:
                # fallback ao detector existente
                base_branch = _get_default_base_branch(repo_path)

        # Buscar remotas para base e para develop (manter ambos atualizados)
        try:
            run_git_command(repo_path, ["fetch", "origin", base_branch])
        except GitCommandError:
            # Se fetch falhar, log e re-raise
            logger.warning(f"Falha ao buscar origin/{base_branch} antes de criar branch.")
            raise

        # Também atualizar develop para segurança, caso base seja main/master
        if base_branch != "develop":
            try:
                run_git_command(repo_path, ["fetch", "origin", "develop"])
            except GitCommandError:
                logger.debug("Não foi possível fetch origin/develop (pode não existir), prosseguindo.")

        # Fazer checkout para a branch base antes de criar a nova branch
        try:
            run_git_command(repo_path, ["checkout", base_branch])
        except GitCommandError:
            # Se a branch local não existir, tentar criar local a partir do remoto (tracking)
            try:
                run_git_command(repo_path, ["checkout", "-b", base_branch, f"origin/{base_branch}"])
            except GitCommandError as e:
                logger.error(f"Falha ao criar/checkoutr base '{base_branch}': {e}")
                raise

        # Criar a nova branch a partir da base atualizada
        run_git_command(repo_path, ["checkout", "-b", branch_name])

        msg = f"🌱 Branch '{branch_name}' criada com sucesso a partir de '{base_branch}'."
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
    return _get_protected_branches()


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


def resolve_conflict(repo_path: str, branch: str, base_branch: str = None, favor: str = "theirs", strategy: str | None = None, preview: bool = False, push: bool = False) -> str:
    """Tenta resolver conflitos automaticamente usando a estratégia de merge option (-X).

    Args:
        repo_path: caminho do repositório
        branch: branch local a atualizar
        base_branch: branch base para sincronização (se None detecta automaticamente)
        favor: 'ours' ou 'theirs' — qual lado priorizar ao resolver conflitos
        strategy: 'rebase' ou 'merge' (se None usa configuração do usuário)

    Returns:
        Mensagem de sucesso

    Raises:
        GitCommandError em caso de falha na resolução automática.
    """
    # Normalize inputs
    if favor not in {"ours", "theirs"}:
        raise GitCommandError(f"Favor inválido: {favor}. Use 'ours' ou 'theirs'.")

    # Determine strategy default
    if not strategy:
        strategy = get_default_strategy()

    # If preview mode, operate on a temporary copy of the repository
    work_dir = repo_path
    temp_dir = None
    try:
        if preview:
            temp_dir = tempfile.mkdtemp(prefix="automatizar_preview_")
            # Try a shallow clone first for performance
            try:
                proc = subprocess.run(["git", "clone", "--depth", "1", repo_path, temp_dir], capture_output=True, text=True)
                if proc.returncode != 0:
                    # Fallback to full clone if shallow clone fails (some git servers or local repos may not support it)
                    proc2 = subprocess.run(["git", "clone", repo_path, temp_dir], capture_output=True, text=True)
                    if proc2.returncode != 0:
                        raise GitCommandError(f"Falha ao clonar repositório para preview: {proc2.stderr.strip()}")
            except Exception as e:
                # As a last resort, fallback to filesystem copy (slower)
                try:
                    shutil.copytree(repo_path, temp_dir, dirs_exist_ok=True)
                except Exception as e2:
                    raise GitCommandError(f"Falha ao preparar preview: {e} / {e2}")
            work_dir = temp_dir

        # Garantir checkout na branch dentro work_dir
        run_git_command(work_dir, ["checkout", branch])

        if not base_branch:
            base_branch = _get_default_base_branch(work_dir)

        # Buscar remotos atualizados
        run_git_command(work_dir, ["fetch", "origin", base_branch])
        run_git_command(work_dir, ["fetch", "origin", branch])

        if strategy == "rebase":
            # Tentar rebase com opção de favor
            try:
                run_git_command(work_dir, ["rebase", "-X", favor, f"origin/{base_branch}"])
            except GitCommandError as e:
                # Tentar abortar para deixar repositório limpo
                try:
                    run_git_command(work_dir, ["rebase", "--abort"])
                except Exception:
                    logger.debug("Falha ao abortar rebase automaticamente durante resolve_conflict.")
                raise GitCommandError(f"Falha ao tentar rebase com favor='{favor}': {e}")

            # Push após rebase se solicitado e não em preview
            if push and not preview:
                run_git_command(work_dir, ["push", "origin", branch, "--force-with-lease"])
                pushed_msg = " e enviado ao remoto"
            else:
                pushed_msg = " (não enviado ao remoto)" if preview or not push else ""

            msg = f"✅ Conflitos resolvidos automaticamente em '{branch}' usando favor='{favor}' (rebase){pushed_msg}."
            logger.info(msg)
            return msg

        elif strategy == "merge":
            try:
                run_git_command(work_dir, ["merge", "-X", favor, f"origin/{base_branch}"])
            except GitCommandError as e:
                # Em caso de falha, tentar abortar merge
                try:
                    run_git_command(work_dir, ["merge", "--abort"])
                except Exception:
                    logger.debug("Falha ao abortar merge automaticamente durante resolve_conflict.")
                raise GitCommandError(f"Falha ao tentar merge com favor='{favor}': {e}")

            if push and not preview:
                run_git_command(work_dir, ["push", "origin", branch])
                pushed_msg = " e enviado ao remoto"
            else:
                pushed_msg = " (não enviado ao remoto)" if preview or not push else ""

            msg = f"✅ Conflitos resolvidos automaticamente em '{branch}' usando favor='{favor}' (merge){pushed_msg}."
            logger.info(msg)
            return msg

        else:
            raise GitCommandError(f"Strategy inválida: {strategy}. Use 'rebase' ou 'merge'.")

    finally:
        # Cleanup temp dir if used
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                logger.debug(f"Falha ao remover tempdir {temp_dir}")
        # End
        pass
