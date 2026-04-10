from core.git_operations import run_git_command, GitCommandError
from core.logger_config import get_logger
from services.branch_service import list_branches, list_remote_branches

logger = get_logger()


def _resolve_local_branch_name(repo_path: str, branch: str) -> str:
    """Resolve a branch name to an existing local branch. If branch doesn't exist,
    try with 'feature/' prefix when appropriate. Returns the resolved name.
    """
    locals_ = list_branches(repo_path)
    if branch in locals_:
        return branch
    # if user passed only the suffix, try feature/<suffix>
    if "/" not in branch:
        candidate = f"feature/{branch}"
        if candidate in locals_:
            return candidate
    # fallback: return original
    return branch


def _resolve_remote_branch_name(repo_path: str, branch: str) -> str:
    remotas = list_remote_branches(repo_path)
    if branch in remotas:
        return branch
    if "/" not in branch:
        candidate = f"feature/{branch}"
        if candidate in remotas:
            return candidate
    return branch


def delete_local_branch(repo_path: str, branch: str) -> str:
    """Deleta uma branch local específica. Resolve automaticamente 'feature/' quando apropriado."""
    resolved = _resolve_local_branch_name(repo_path, branch)
    if resolved in {"main", "master", "develop"}:
        raise GitCommandError(f"⚠️ A branch '{resolved}' é protegida e não pode ser deletada.")
    try:
        run_git_command(repo_path, ["branch", "-D", resolved])
        return f"🗑️ Branch local '{resolved}' removida."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar branch local '{resolved}': {e}")


def delete_all_local_branches(repo_path: str) -> str:
    """Deleta todas as branches locais, exceto as protegidas."""
    try:
        raw = run_git_command(repo_path, ["branch"]).splitlines()
        locals_ = [b.replace("*", "").strip() for b in raw if b.strip()]
        protegidas = {"main", "master", "develop"}
        deletadas = []

        for br in locals_:
            if br not in protegidas:
                run_git_command(repo_path, ["branch", "-D", br])
                deletadas.append(br)

        if deletadas:
            return f"🧹 Branches locais deletadas: {', '.join(deletadas)}"
        else:
            return "Nenhuma branch deletada (todas protegidas)."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar todas as branches locais: {e}")


def delete_remote_branch(repo_path: str, branch: str) -> str:
    """Deleta uma branch remota. Resolve automaticamente 'feature/' quando apropriado."""
    resolved = _resolve_remote_branch_name(repo_path, branch)
    if resolved in {"main", "master", "develop"}:
        raise GitCommandError(f"⚠️ '{resolved}' é protegida e não pode ser deletada.")
    try:
        run_git_command(repo_path, ["push", "origin", "--delete", resolved])
        return f"🗑️ Branch remota '{resolved}' deletada com sucesso."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar branch remota '{resolved}': {e}")


def delete_all_remote_branches(repo_path: str) -> str:
    """Deleta todas as branches remotas não protegidas."""
    try:
        raw = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        remotas = [b.strip().replace("origin/", "") for b in raw if "origin/" in b and "HEAD" not in b]
        protegidas = {"main", "master", "develop"}
        deletadas = []

        for br in remotas:
            if br not in protegidas:
                try:
                    run_git_command(repo_path, ["push", "origin", "--delete", br])
                    deletadas.append(br)
                except GitCommandError as e:
                    logger.warning(f"⚠️ Não foi possível deletar '{br}': {e}")

        if deletadas:
            return f"🧹 Branches remotas deletadas: {', '.join(deletadas)}"
        else:
            return "Nenhuma branch remota deletada (todas protegidas)."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar todas as branches remotas: {e}")
