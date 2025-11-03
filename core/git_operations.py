# core/git_operations.py
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv


# =====================================================
# Exceção personalizada para erros Git
# =====================================================
class GitCommandError(Exception):
    pass


# =====================================================
# Funções utilitárias principais
# =====================================================
def run_git_command(repo_path, args):
    """
    Executa um comando Git e retorna a saída.
    Lança GitCommandError em caso de erro.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        log_output(repo_path, args, result)
        if result.returncode != 0:
            raise GitCommandError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()
    except Exception as e:
        raise GitCommandError(f"Erro ao executar git {' '.join(args)}: {e}")


def log_output(repo_path, args, result):
    """Loga no console interno (debug opcional)"""
    print(f"[{repo_path}] $ git {' '.join(args)}")
    if result.stdout:
        print("Saída:", result.stdout.strip())
    if result.stderr:
        print("Erro:", result.stderr.strip())


# =====================================================
# Configuração automática do token
# =====================================================
def configure_remote_with_token(repo_path):
    """
    Injeta o token do .env na URL remota se o repositório usa HTTPS.
    Exemplo: transforma
      https://github.com/usuario/repositorio.git
    em:
      https://<TOKEN>:x-oauth-basic@github.com/usuario/repositorio.git
    """
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN não configurado no .env")
        return

    try:
        # Verifica URL remota atual
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()

        # Se já contém token, não faz nada
        if "@" in url or url.startswith("git@"):
            return

        if url.startswith("https://"):
            new_url = url.replace("https://", f"https://{token}:x-oauth-basic@")
            subprocess.run(["git", "remote", "set-url", "origin", new_url], cwd=repo_path)
            print(f"✅ URL remota configurada com token para {repo_path}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Não foi possível verificar/configurar remoto: {e}")


# =====================================================
# Funções Git principais
# =====================================================
def get_current_branch(repo_path):
    """Obtém o nome da branch atual."""
    output = run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    return output.strip()


def create_branch(repo_path, branch_name):
    """Cria uma nova branch a partir da atual."""
    run_git_command(repo_path, ["checkout", "-b", branch_name])
    return branch_name


def commit_and_push(repo_path, message):
    """
    Realiza git add, commit e push.
    Configura automaticamente o token HTTPS.
    """
    configure_remote_with_token(repo_path)

    run_git_command(repo_path, ["add", "."])
    run_git_command(repo_path, ["commit", "-m", message])

    branch = get_current_branch(repo_path)
    run_git_command(repo_path, ["push", "-u", "origin", branch])
    remote = get_remote_name(repo_path)
    return branch, remote


def get_remote_name(repo_path):
    """Retorna o nome do remoto configurado (geralmente 'origin')."""
    output = run_git_command(repo_path, ["remote"])
    lines = output.splitlines()
    return lines[0] if lines else "origin"


def merge_to_main(repo_path, branch_name):
    """
    Faz merge da branch informada na main (local).
    """
    run_git_command(repo_path, ["checkout", "main"])
    run_git_command(repo_path, ["merge", branch_name])
    return "main"
