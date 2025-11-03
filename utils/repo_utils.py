# utils/repo_utils.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import configparser
import re
from typing import Optional, Tuple

class RepoConfigError(Exception):
    """Erros relacionados à leitura do .git/config."""
    pass

class RemoteUrlParseError(Exception):
    """Erros relacionados ao parse da URL remota do Git."""
    pass

@dataclass(frozen=True)
class RepoInfo:
    host: str         # ex.: github.com ou github.empresa.com
    owner: str        # ex.: usuario / organização
    name: str         # ex.: repositorio (sem .git)
    remote: str = "origin"

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

def _read_git_config(repo_path: Path) -> configparser.ConfigParser:
    """
    Lê o arquivo .git/config do repositório informado.
    :param repo_path: caminho da pasta RAIZ do repositório (onde existe a pasta .git)
    """
    repo_path = Path(repo_path).expanduser().resolve()
    git_dir = repo_path / ".git"
    config_path = git_dir / "config"

    if not git_dir.exists() or not git_dir.is_dir():
        raise RepoConfigError(f"Diretório .git não encontrado em: {repo_path}")

    if not config_path.exists() or not config_path.is_file():
        raise RepoConfigError(f"Arquivo .git/config não encontrado em: {config_path}")

    parser = configparser.RawConfigParser()
    # Respeita case e chaves repetidas de seção remota
    with config_path.open("r", encoding="utf-8") as f:
        parser.read_file(f)
    return parser

def _get_remote_url_from_config(cfg: configparser.ConfigParser, remote: str = "origin") -> str:
    """
    Obtém a URL do remote (default: origin).
    Suporta múltiplas entradas de remote (formato: [remote "origin"]).
    """
    remote_section = f'remote "{remote}"'
    if not cfg.has_section(remote_section):
        # fallback: tentar seções que comecem com remote "
        sections = [s for s in cfg.sections() if s.startswith('remote "')]
        available = ", ".join(sections) if sections else "(nenhuma remota encontrada)"
        raise RepoConfigError(f"Seção {remote_section} não encontrada em .git/config. Remotas: {available}")

    try:
        return cfg.get(remote_section, "url")
    except (configparser.NoOptionError, ValueError):
        raise RepoConfigError(f"Chave 'url' não encontrada na seção {remote_section}.")

def _strip_dot_git(name: str) -> str:
    return name[:-4] if name.endswith(".git") else name

def _parse_https(url: str) -> Tuple[str, str, str]:
    """
    HTTPS: https://<host>/<owner>/<repo>.git?
    Ex: https://github.com/usuario/repositorio.git
    """
    # Permite paths extras (ex.: /scm/) comuns em servidores enterprise
    m = re.match(r"^https?://([^/]+)/(.+?)$", url, flags=re.IGNORECASE)
    if not m:
        raise RemoteUrlParseError("URL HTTPS inválida.")

    host = m.group(1).strip()
    path = m.group(2).strip().strip("/")

    # Alguns servidores usam prefixos como "scm" ou "git". Vamos manter genérico:
    parts = path.split("/")
    if len(parts) < 2:
        raise RemoteUrlParseError(f"Path HTTPS inesperado: '{path}'")

    owner = parts[-2]
    repo = _strip_dot_git(parts[-1])
    return host, owner, repo

def _parse_ssh(url: str) -> Tuple[str, str, str]:
    """
    SSH: git@<host>:<owner>/<repo>.git  OU  ssh://git@<host>/<owner>/<repo>.git
    """
    # Forma 1: git@host:owner/repo(.git)
    m = re.match(r"^[\w\-\.]+@([^:]+):(.+)$", url, flags=re.IGNORECASE)
    if m:
        host = m.group(1).strip()
        path = m.group(2).strip().strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise RemoteUrlParseError(f"Path SSH inesperado: '{path}'")
        owner = parts[-2]
        repo = _strip_dot_git(parts[-1])
        return host, owner, repo

    # Forma 2: ssh://git@host/owner/repo(.git)
    m2 = re.match(r"^ssh://[\w\-\.]+@([^/]+)/(.+)$", url, flags=re.IGNORECASE)
    if m2:
        host = m2.group(1).strip()
        path = m2.group(2).strip().strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise RemoteUrlParseError(f"Path SSH inesperado: '{path}'")
        owner = parts[-2]
        repo = _strip_dot_git(parts[-1])
        return host, owner, repo

    raise RemoteUrlParseError("URL SSH inválida ou formato não suportado.")

def parse_remote_url(url: str) -> Tuple[str, str, str]:
    """
    Retorna (host, owner, repo) a partir de uma URL remota HTTPS ou SSH.
    """
    url = url.strip()
    if url.startswith(("http://", "https://")):
        return _parse_https(url)
    if url.startswith(("git@", "ssh://")):
        return _parse_ssh(url)
    # Caso raro: file:// ou caminhos locais — não suportamos PR para esses casos
    raise RemoteUrlParseError(f"Esquema de URL não suportado: {url}")

def get_repo_info(repo_path: str | Path, remote: str = "origin") -> RepoInfo:
    """
    API principal: lê .git/config e retorna RepoInfo(host, owner, name, remote)

    Uso:
        info = get_repo_info("/caminho/do/repo")
        print(info.host, info.owner, info.name, info.full_name)
    """
    cfg = _read_git_config(Path(repo_path))
    url = _get_remote_url_from_config(cfg, remote=remote)
    host, owner, name = parse_remote_url(url)
    return RepoInfo(host=host, owner=owner, name=name, remote=remote)

# -----------------------
# Helpers opcionais
# -----------------------

def try_get_repo_info(repo_path: str | Path, remote: str = "origin") -> Optional[RepoInfo]:
    """
    Variante tolerante a falhas: retorna None se não conseguir extrair.
    Útil para UI onde queremos exibir uma mensagem amigável sem quebrar o fluxo.
    """
    try:
        return get_repo_info(repo_path, remote=remote)
    except (RepoConfigError, RemoteUrlParseError):
        return None
