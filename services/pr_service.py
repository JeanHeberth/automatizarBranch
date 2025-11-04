from core.pr_operations import create_pull_request
from core.git_operations import merge_pull_request, GitCommandError


def create_pr(repo_path: str, base: str, title: str) -> str:
    """Cria um Pull Request."""
    try:
        url = create_pull_request(repo_path, base, title)
        return f"Pull Request criado com sucesso!\n{url}"
    except Exception as e:
        raise GitCommandError(f"Erro ao criar PR: {e}")


def merge_pr(repo_path: str, pr_number: int) -> str:
    """Realiza o merge de um PR existente."""
    try:
        return merge_pull_request(repo_path, pr_number)
    except Exception as e:
        raise GitCommandError(f"Erro ao mesclar PR: {e}")
