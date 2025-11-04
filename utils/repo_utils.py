import os
import re


class RepoInfo:
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name


def get_repo_info(repo_path):
    """Extrai owner e nome do repositório a partir do remoto."""
    git_config = (os.popen(f"cd {repo_path} && git remote get-url origin")
                  .read().strip())
    match = re.search(r"github\.com[:/](.*?)/(.*?)(\.git)?$", git_config)
    if not match:
        raise RuntimeError("Repositório remoto inválido ou não configurado.")
    owner, name = match.group(1), match.group(2)
    return RepoInfo(owner, name)
