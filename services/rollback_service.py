from core.git_operations import rollback_last_commit, discard_local_changes, GitCommandError


def rollback_commit(repo_path: str, soft: bool = True) -> str:
    """Desfaz o último commit."""
    try:
        mode = "soft" if soft else "hard"
        branch = rollback_last_commit(repo_path, mode=mode)
        tipo = "leve" if soft else "completo"
        return f"Rollback ({tipo}) concluído na branch {branch}."
    except Exception as e:
        raise GitCommandError(f"Erro ao realizar rollback de commit: {e}")


def rollback_changes(repo_path: str) -> str:
    """Desfaz alterações locais não commitadas."""
    try:
        discard_local_changes(repo_path)
        return "Alterações locais descartadas com sucesso."
    except Exception as e:
        raise GitCommandError(f"Erro ao descartar alterações: {e}")
