import configparser
from pathlib import Path
from typing import NamedTuple


class RepoInfo(NamedTuple):
    user: str
    repo: str
    full_name: str


def get_repo_info(repo_path: Path) -> RepoInfo:
    """Extrai user/repo da configuração Git local (.git/config)."""
    config = configparser.ConfigParser()
    config.read(Path(repo_path) / ".git" / "config", encoding="utf-8")

    try:
        url = config["remote \"origin\""]["url"]
        # Suporta formatos SSH e HTTPS
        if url.startswith("git@"):
            path = url.split(":")[1].replace(".git", "")
        else:
            path = url.split("github.com/")[1].replace(".git", "")
        user, repo = path.split("/")
        return RepoInfo(user=user, repo=repo, full_name=f"{user}/{repo}")
    except Exception:
        raise RuntimeError("Não foi possível extrair user/repo de .git/config.")
