import os
import tkinter as tk
from tkinter import Toplevel
from tkinter import ttk, messagebox
from dotenv import load_dotenv
import requests


from utils import run_command


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

    feature_branch = f"{nome}"
    run_command(f"git checkout {branch_main}")
    run_command("git pull")
    run_command(f"git checkout -b {feature_branch}")

    if branch_remota_existe("develop"):
        run_command("git pull origin develop")

    return True, f"Branch '{feature_branch}' criada com sucesso."


def fazer_commit(mensagem):
    from utils import run_command

    run_command("git add -A")
    stdout, stderr = run_command(f'git commit -m "{mensagem}"')

    if "nothing to commit" in (stdout + stderr).lower():
        return False, "Nenhuma modificação para commit."

    if stderr:
        return False, stderr

    return True, stdout or "Commit realizado com sucesso."

def push():
    branch_atual, _ = run_command("git rev-parse --abbrev-ref HEAD")

    # Tenta fazer push normalmente
    stdout, stderr = run_command("git push")

    # Se falhar por ausência de upstream, faz push com -u
    if "set upstream" in stderr.lower() or "no upstream" in stderr.lower():
        stdout, stderr = run_command(f"git push -u origin {branch_atual.strip()}")

    if stderr:
        return False, stderr
    return True, stdout or "Push realizado com sucesso."
def atualizar_branch():
    branches = listar_branches()
    if not branches:
        messagebox.showerror("Erro", "Nenhuma branch encontrada.")
        return

    popup = Toplevel()
    popup.title("Atualizar Branch")
    popup.geometry("400x150")
    popup.grab_set()

    tk.Label(popup, text="Selecione uma branch para atualizar:").pack(pady=10)

    branch_var = tk.StringVar()
    combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
    combo.pack(pady=5)
    combo.set(branches[0])

    def confirmar():
        branch = branch_var.get()
        popup.destroy()
        if branch:
            run_command(f"git checkout {branch}")
            stdout, stderr = run_command(f"git pull origin {branch}")
            if stderr:
                messagebox.showerror("Erro", stderr)
            else:
                messagebox.showinfo("Atualizado", f"Branch '{branch}' atualizada com sucesso.")

    tk.Button(popup, text="Atualizar", command=confirmar, width=10).pack(pady=10)


def listar_branches():
    stdout, _ = run_command("git branch --list")
    return [linha.strip().lstrip("* ") for linha in stdout.splitlines() if linha.strip()]


def fazer_checkout(branch):
    out, err = run_command(f"git checkout {branch}")

    if "error" in out.lower() or "fatal" in out.lower() or err:
        return False, f"Erro ao trocar para a branch '{branch}'. Saída: {out or err}"

    return True, f"Checkout realizado com sucesso para '{branch}'"





def deletar_branches_locais():
    stdout, _ = run_command("git branch")
    all_branches = [b.strip("* ").strip() for b in stdout.splitlines()]

    protegidas = {"main", "master", "develop"}
    mensagens = []

    for branch in all_branches:
        if branch in protegidas:
            continue
        out, err = run_command(f"git branch -D {branch}")
        mensagens.append(
            f"✅ {branch} deletada." if not err else f"⚠️ Erro ao deletar {branch}: {err}"
        )

    return "\n".join(mensagens)

def deletar_branch_remota(branch):
    protegidas = {"main", "master", "develop"}
    if branch in protegidas:
        return False, f"Branch protegida: {branch}"

    if branch_remota_existe(branch):
        out, err = run_command(f"git push origin --delete {branch}")
        if err:
            return False, f"Erro ao deletar '{branch}': {err}"
        return True, f"Branch remota '{branch}' deletada com sucesso."

    return False, f"Branch '{branch}' não existe remotamente."

def confirmar():
    branch = branch_v

    if branch in {"main", "master", "develop"}:
       messagebox.showwarning("Aviso", f"Branch protegida: {branch}")
    elif branch_remota_existe(branch):
       out, err = run_command(f"git push origin --delete {branch}")
       if err:
           messagebox.showerror("Erro", err)
       else:
           messagebox.showinfo("Deletada", f"Branch remota '{branch}' deletada com sucesso.")
    else:
       messagebox.showinfo("Aviso", f"Branch '{branch}' não existe remotamente.")



load_dotenv()
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "JeanHeberth"  # Substitua pelo seu usuário
REPO_NAME = "automatizarBranch"  # Substitua pelo nome do seu repositório

def criar_pull_request(branch_origem, branch_destino="main", titulo="Novo PR", corpo="PR criado automaticamente"):
    if not GITHUB_TOKEN:
        return False, "Token do GitHub não encontrado."

    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "title": titulo,
        "body": corpo,
        "head": branch_origem,
        "base": branch_destino
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return True, f"✅ Pull Request criado: {response.json().get('html_url')}"
    else:
        erro = response.json().get("message", "Erro desconhecido")
        return False, f"❌ Erro ao criar PR: {erro}"
