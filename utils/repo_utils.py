from pathlib import Path
from collections import namedtuple
import subprocess

RepoInfo = namedtuple("RepoInfo", ["user", "repo", "full_name", "current_branch"])


def get_repo_info(repo_path: Path) -> RepoInfo:
    """Lê .git/config e retorna usuário, repositório e branch atual."""
    config_path = Path(repo_path) / ".git" / "config"

    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {config_path}")

    user = repo = None
    with open(config_path, "r") as f:
        for line in f:
            if "url =" in line:
                url = line.split("=", 1)[1].strip()
                if "github.com" in url:
                    if url.startswith("git@github.com:"):
                        parts = url.split(":")[1].replace(".git", "").split("/")
                    else:
                        parts = url.split("github.com/")[1].replace(".git", "").split("/")
                    user, repo = parts[0], parts[1]
                break

    if not user or not repo:
        raise ValueError("Não foi possível determinar o repositório GitHub.")

    # 🔥 Agora pegamos a branch diretamente via subprocess (sem importar core)
    try:
        branch = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        branch = "desconhecida"

    return RepoInfo(user=user, repo=repo, full_name=f"{user}/{repo}", current_branch=branch)
