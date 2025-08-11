from tkinter import Toplevel
from tkinter import Toplevel
from tkinter import ttk

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

def deletar_branch_remota_com_mensagem(branch):
    if branch in {"main", "master", "develop"}:
        return False, f"Branch protegida: {branch}"
    elif branch_remota_existe(branch):
        out, err = run_command(f"git push origin --delete {branch}")
        if err:
            return False, err
        else:
            return True, f"Branch remota '{branch}' deletada com sucesso."
    else:
        return False, f"Branch '{branch}' não existe remotamente."


def deletar_branch_local_com_mensagem(branch):
    """
    Deleta uma branch local com mensagem personalizada
    """
    from tkinter import messagebox, simpledialog
    
    # Verificar se a branch existe localmente
    branches = listar_branches()
    if branch not in branches:
        messagebox.showerror("Erro", f"Branch '{branch}' não existe localmente.")
        return False
    
    # Verificar se não é a branch atual
    current_branch = get_current_branch()
    if branch == current_branch:
        messagebox.showerror("Erro", f"Não é possível deletar a branch atual '{branch}'. Faça checkout para outra branch primeiro.")
        return False
    
    # Solicitar mensagem de confirmação
    mensagem = simpledialog.askstring(
        "Confirmar Deleção", 
        f"Digite uma mensagem para confirmar a deleção da branch '{branch}':",
        initialvalue=f"Deletando branch local {branch}"
    )
    
    if not mensagem:
        messagebox.showinfo("Cancelado", "Deleção cancelada pelo usuário.")
        return False
    
    # Executar comando para deletar a branch local
    success, output = run_command(f"git branch -d {branch}")
    
    if success:
        messagebox.showinfo("Sucesso", f"Branch '{branch}' deletada localmente com sucesso.\nMensagem: {mensagem}")
        return True
    else:
        # Tentar forçar a deleção se a deleção normal falhar
        force_success, force_output = run_command(f"git branch -D {branch}")
        if force_success:
            messagebox.showwarning("Sucesso (Forçado)", f"Branch '{branch}' foi forçadamente deletada localmente.\nMensagem: {mensagem}\nAviso: A branch pode ter commits não mesclados.")
            return True
        else:
            messagebox.showerror("Erro", f"Erro ao deletar branch '{branch}' localmente:\n{force_output}")
            return False


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



def deletar_branch_remota(branch):
    if branch in {"main", "master", "develop"}:
        return False, f"Branch protegida: {branch}"

    if branch_remota_existe(branch):
        out, err = run_command(f"git push origin --delete {branch}")
        if err:
            return False, f"Erro ao deletar '{branch}': {err}"
        return True, f"Branch remota '{branch}' deletada com sucesso."

    return False, f"Branch '{branch}' não existe remotamente."


import os
import requests
from dotenv import load_dotenv
import tkinter as tk
from tkinter import simpledialog, messagebox

# Carrega variáveis do .env
load_dotenv()

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "JeanHeberth"  # Substitua pelo seu usuário
REPO_NAME = "automatizarBranch"  # Substitua pelo nome do seu repositório

def criar_pull_request(branch_origem, branch_destino="main", titulo="Novo PR", corpo="PR criado automaticamente"):
    if not GITHUB_TOKEN:
        return False, "❌ Token do GitHub não encontrado. Verifique o arquivo .env"
    
    # Obter configuração dinamicamente do repositório atual
    from utils import get_repo_config
    config = get_repo_config()
    if not config:
        return False, "❌ Configuração do repositório não encontrada"
    
    REPO_OWNER = config.get('usuario')
    REPO_NAME = config.get('repositorio')
    
    if not REPO_OWNER or not REPO_NAME:
        return False, "❌ Usuário ou repositório não configurados no .git-config.json

    # Validações básicas
    if not branch_origem or not branch_destino:
        return False, "❌ Branches de origem e destino são obrigatórias"
    
    if branch_origem == branch_destino:
        return False, "❌ Branch de origem e destino não podem ser iguais"

    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "title": titulo,
        "body": corpo,
        "head": branch_origem,
        "base": branch_destino
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 201:
            pr_data = response.json()
            pr_url = pr_data.get('html_url')
            pr_number = pr_data.get('number')

            # Loga o número do PR
            with open("log.txt", "a") as log:
                log.write(f"[PR CRIADO] Número: #{pr_number} | URL: {pr_url}\n")

            return True, f"✅ Pull Request #{pr_number} criado com sucesso!\n🔗 URL: {pr_url}"
        
        elif response.status_code == 422:
            # Erro comum quando já existe um PR ou há conflitos
            try:
                error_data = response.json()
                erro = error_data.get("message", "Erro de validação")
                if "pull request already exists" in erro.lower():
                    return False, f"❌ Já existe um Pull Request aberto entre {branch_origem} e {branch_destino}"
                else:
                    return False, f"❌ Erro de validação: {erro}"
            except:
                return False, "❌ Erro de validação (422) - Verifique se as branches existem"
        
        elif response.status_code == 401:
            return False, "❌ Token do GitHub inválido ou expirado"
        
        elif response.status_code == 404:
            return False, f"❌ Repositório {REPO_OWNER}/{REPO_NAME} não encontrado ou sem acesso"
        
        else:
            try:
                error_data = response.json()
                erro = error_data.get("message", "Erro desconhecido")
                return False, f"❌ Erro ao criar PR ({response.status_code}): {erro}"
            except:
                return False, f"❌ Erro HTTP {response.status_code} ao criar Pull Request"
                
    except requests.exceptions.Timeout:
        return False, "❌ Timeout na requisição - Verifique sua conexão com a internet"
    except requests.exceptions.ConnectionError:
        return False, "❌ Erro de conexão - Verifique sua conexão com a internet"
    except Exception as e:
        return False, f"❌ Erro inesperado: {str(e)}"

def merge_pull_request(numero_pr):
    if not GITHUB_TOKEN:
        return False, "❌ Token do GitHub não encontrado. Verifique o arquivo .env
    
    # Obter configuração dinamicamente
    from utils import get_repo_config
    config = get_repo_config()
    if not config:
        return False, "❌ Configuração do repositório não encontrada"
    
    REPO_OWNER = config.get('usuario')
    REPO_NAME = config.get('repositorio')
   
    # Validação básica
    if not numero_pr:
        return False, "❌ Número do Pull Request é obrigatório"
    
    try:
        numero_pr = int(numero_pr)
    except (ValueError, TypeError):
        return False, "❌ Número do Pull Request deve ser um número válido"

    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{numero_pr}/merge"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Payload para o merge
    payload = {
        "commit_title": f"Merge pull request #{numero_pr}",
        "merge_method": "merge"  # Pode ser 'merge', 'squash' ou 'rebase'
    }

    try:
        response = requests.put(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            merge_data = response.json()
            commit_sha = merge_data.get('sha', 'N/A')
            
            # Loga o merge
            with open("log.txt", "a") as log:
                log.write(f"[PR MERGED] Número: #{numero_pr} | Commit: {commit_sha}\n")
            
            return True, f"✅ Pull Request #{numero_pr} mergeado com sucesso!\n📝 Commit: {commit_sha[:8]}"
        
        elif response.status_code == 405:
            return False, f"❌ Pull Request #{numero_pr} não pode ser mergeado\n(pode estar fechado, já mergeado ou ter conflitos)"
        
        elif response.status_code == 404:
            return False, f"❌ Pull Request #{numero_pr} não encontrado no repositório {REPO_OWNER}/{REPO_NAME}"
        
        elif response.status_code == 401:
            return False, "❌ Token do GitHub inválido ou sem permissão para fazer merge"
        
        elif response.status_code == 409:
            return False, f"❌ Pull Request #{numero_pr} tem conflitos que precisam ser resolvidos primeiro"
        
        else:
            try:
                error_data = response.json()
                erro = error_data.get("message", "Erro desconhecido")
                return False, f"❌ Erro ao fazer merge do PR #{numero_pr} ({response.status_code}): {erro}"
            except:
                return False, f"❌ Erro HTTP {response.status_code} ao fazer merge do Pull Request #{numero_pr}"
                
    except requests.exceptions.Timeout:
        return False, "❌ Timeout na requisição - Verifique sua conexão com a internet"
    except requests.exceptions.ConnectionError:
        return False, "❌ Erro de conexão - Verifique sua conexão com a internet"
    except Exception as e:
        return False, f"❌ Erro inesperado ao fazer merge: {str(e)}"

