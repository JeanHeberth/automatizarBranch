from tkinter import Toplevel
import tkinter as tk
from tkinter import ttk, messagebox


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

    run_command(f"git checkout -b {feature_branch}")

    if branch_remota_existe("develop"):
        run_command("git pull origin develop")

    return True, f"Branch '{feature_branch}' criada com sucesso."

def fazer_commit(mensagem):
    run_command("git add -A")
    run_command(f'git commit -m "{mensagem}"')
    return True, "Commit realizado com sucesso."

def push():
    branch = get_current_branch()
    run_command(f"git push origin {branch}")
    return True, f"Push feito para a branch {branch}."

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
            listar_branches()
            popup.destroy()
            if branch:
                run_command(f"git checkout {branch}")
                stdout, stderr = run_command(f"git pull origin {branch}")

                if stderr:
                    messagebx.showerror("Erro", stderr)
                else:
                    messagebox.showinfo("Atualizado", f"Branch '{branch}' atualizada com sucesso.")

        tk.Button(popup, text="Atualizar", command=confirmar, width=10).pack(pady=10)


def listar_branches():
    stdout, _ = run_command("git branch --list")
    return [linha.strip().lstrip("* ") for linha in stdout.splitlines() if linha.strip()]

def fazer_checkout(branch_nome):
    stdout, stderr = run_command(f"git checkout {branch_nome}")
    saida_total = f"{stdout}\n{stderr}".lower()

    sucesso = (
            "switched to" in saida_total or
            "already on" in saida_total
    )

    return sucesso, stderr or stdout


