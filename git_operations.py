from utils import run_command, get_repo_path, log
import os

def get_default_branch():
    stdout, _ = run_command("git symbolic-ref refs/remotes/origin/HEAD")
    if stdout:
        return stdout.split("/")[-1]
    branches, _ = run_command("git branch -r")
    if "origin/main" in branches:
        return "main"
    elif "origin/master" in branches:
        return "master"
    return None

def branch_remota_existe(branch):
    stdout, _ = run_command(f"git ls-remote --heads origin {branch}")
    return branch in stdout

def get_current_branch():
    stdout, _ = run_command("git rev-parse --abbrev-ref HEAD")
    return stdout

def criar_branch(nome):
    branch_main = get_default_branch()
    if not branch_main:
        return False, "Branch principal não detectada."

    feature_branch = f"feature/{nome}"
    run_command(f"git checkout {branch_main}")
    run_command("git pull")

    if os.name != "nt":
        run_command(f"git branch | grep -v '{branch_main}' | xargs git branch -D")

    run_command(f"git checkout -b {feature_branch}")

    if branch_remota_existe("develop"):
        run_command("git pull origin develop")

    return True, f"Branch '{feature_branch}' criada com sucesso."

def fazer_commit(mensagem):
    run_command("git add .")
    run_command(f'git commit -m "{mensagem}"')
    return True, "Commit realizado com sucesso."

def push():
    branch = get_current_branch()
    run_command(f"git push origin {branch}")
    return True, f"Push feito para a branch {branch}."

def atualizar_branch_principal():
    branch_main = get_default_branch()
    if not branch_main:
        return False, "Não foi possível identificar a branch principal."
    run_command(f"git checkout {branch_main}")
    run_command(f"git pull origin {branch_main}")
    return True, f"Branch principal '{branch_main}' atualizada com sucesso."

