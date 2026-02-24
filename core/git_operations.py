import subprocess
import requests
from pathlib import Path
from typing import List
from core.env_utils import require_github_token
from utils.repo_utils import get_repo_info
from core.logger_config import get_logger

logger = get_logger()


class GitCommandError(Exception):
    """Erro personalizado para falhas em comandos Git."""
    pass


def run_git_command(repo_path: str, command_list: List[str]) -> str:
    """Executa comandos Git e retorna a saída limpa."""
    try:
        logger.debug(f"Executando: git {' '.join(command_list)}")
        result = subprocess.run(
            ["git", "-C", repo_path] + command_list,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Comando Git falhou: {result.stderr.strip()}")
            raise GitCommandError(result.stderr.strip())
        logger.debug(f"Comando Git sucesso: {result.stdout.strip()[:100]}")
        return result.stdout.strip()
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro ao executar comando Git: {e}")
        raise GitCommandError(str(e))


def get_current_branch(repo_path: str) -> str:
    """Retorna o nome da branch atual."""
    try:
        branch = run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        logger.debug(f"Branch atual: {branch}")
        return branch
    except GitCommandError as e:
        logger.error(f"Erro ao obter branch atual: {e}")
        raise


def rollback_last_commit(repo_path: Path, mode: str = "soft") -> str:
    """Desfaz o último commit."""
    try:
        logger.info(f"Realizando rollback {mode} do último commit...")
        branch = get_current_branch(repo_path)
        if mode == "soft":
            run_git_command(repo_path, ["reset", "--soft", "HEAD~1"])
        elif mode == "hard":
            run_git_command(repo_path, ["fetch", "origin", branch])
            run_git_command(repo_path, ["reset", "--hard", f"origin/{branch}"])
        else:
            raise ValueError("Modo inválido. Use 'soft' ou 'hard'.")
        logger.info(f"Rollback {mode} realizado com sucesso em {branch}")
        return branch
    except Exception as e:
        logger.error(f"Erro ao fazer rollback: {e}")
        raise


def discard_local_changes(repo_path: Path) -> None:
    """Descarta alterações locais não commitadas."""
    try:
        logger.info("Descartando alterações locais...")
        try:
            run_git_command(repo_path, ["restore", "."])
        except GitCommandError:
            run_git_command(repo_path, ["checkout", "--", "."])
        logger.info("Alterações locais descartadas")
    except Exception as e:
        logger.error(f"Erro ao descartar alterações: {e}")
        raise


def merge_pull_request(repo_path: Path, pr_number: int) -> str:
    """Faz o merge de um Pull Request via GitHub API."""
    try:
        logger.info(f"Mesclando PR #{pr_number}...")
        # ✨ Usar autenticação segura via GitHub CLI
        from core.github_auth import get_github_token
        token = get_github_token()

        if not token:
            raise GitCommandError("Falha ao obter autenticação GitHub")

        info = get_repo_info(repo_path)
        url = f"https://api.github.com/repos/{info.full_name}/pulls/{pr_number}/merge"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        response = requests.put(url, headers=headers, json={"merge_method": "squash"})

        if response.status_code == 200:
            msg = f"✅ PR #{pr_number} mesclado com sucesso!"
            logger.info(msg)
            return msg
        elif response.status_code == 405:
            logger.warning(f"PR #{pr_number} já foi mesclado ou está fechado")
            raise GitCommandError(f"PR #{pr_number} já foi mesclado ou está fechado.")
        else:
            logger.error(f"Erro ao mesclar PR #{pr_number}: {response.text}")
            raise GitCommandError(f"Erro ao mesclar PR #{pr_number}: {response.text}")
    except GitCommandError:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao mesclar PR: {e}")
        raise GitCommandError(str(e))


def get_default_main_branch(repo_path: Path) -> str:
    """
    Detecta automaticamente a branch principal (ex: main, master, develop, etc.).
    Verifica a configuração remota e retorna o nome correto.
    """
    try:
        logger.debug("Detectando branch principal...")
        # 1️⃣ tenta ler a branch padrão definida no remoto
        result = run_git_command(repo_path, ["symbolic-ref", "refs/remotes/origin/HEAD"])
        # Exemplo de saída: "refs/remotes/origin/main"
        branch = result.split("/")[-1].strip()
        logger.info(f"Branch principal detectada: {branch}")
        return branch
    except (GitCommandError, Exception) as e:
        logger.debug(f"Falha ao detectar branch via symbolic-ref: {e}, usando fallback...")
        # 2️⃣ fallback — verifica quais branches existem e escolhe a mais provável
        remotas = run_git_command(repo_path, ["branch", "-r"]).splitlines()
        remotas = [b.strip().replace("origin/", "") for b in remotas if "origin/" in b]

        for name in ["main", "master", "develop", "production"]:
            if name in remotas:
                logger.info(f"Branch principal (fallback 1): {name}")
                return name

        # 3️⃣ fallback final — retorna a primeira da lista
        if remotas:
            logger.info(f"Branch principal (fallback 2): {remotas[0]}")
            return remotas[0]

        logger.warning("Nenhuma branch principal detectada, usando 'main'")
        return "main"
