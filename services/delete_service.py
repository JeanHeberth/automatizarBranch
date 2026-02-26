from core.git_operations import run_git_command, GitCommandError


def delete_local_branch(repo_path: str, branch: str) -> str:
    """Deleta uma branch local específica."""
    if branch in {"main", "master", "develop"}:
        raise GitCommandError(f"⚠️ A branch '{branch}' é protegida e não pode ser deletada.")
    try:
        run_git_command(repo_path, ["branch", "-D", branch])
        return f"🗑️ Branch local '{branch}' removida."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar branch local '{branch}': {e}")


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
    """Deleta uma branch remota."""
    if branch in {"main", "master", "develop"}:
        raise GitCommandError(f"⚠️ '{branch}' é protegida e não pode ser deletada.")
    try:
        run_git_command(repo_path, ["push", "origin", "--delete", branch])
        return f"🗑️ Branch remota '{branch}' deletada com sucesso."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar branch remota '{branch}': {e}")


def delete_all_remote_branches(repo_path: str) -> str:
    """Deleta todas as branches remotas, exceto as protegidas."""
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
                except Exception as e:
                    print(f"⚠️ Não foi possível deletar '{br}': {e}")

        if deletadas:
            return f"🧹 Branches remotas deletadas: {', '.join(deletadas)}"
        else:
            return "Nenhuma branch remota deletada (todas protegidas)."
    except Exception as e:
        raise GitCommandError(f"Erro ao deletar todas as branches remotas: {e}")
