import subprocess
import os
import datetime

repo_path = ""
log_file = "git_automation.log"


def set_repo_path(path):
    global repo_path
    repo_path = path


def get_repo_path():
    return repo_path


import json


import json

def get_repo_config():
    config_path = os.path.join(get_repo_path(), ".git-config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)

    # Solicita ao usuário e salva
    from tkinter import simpledialog, messagebox
    usuario = simpledialog.askstring("Usuário GitHub", "Digite seu nome de usuário no GitHub:")
    repositorio = simpledialog.askstring("Repositório GitHub", "Digite o nome do repositório (sem .git):")

    if not usuario or not repositorio:
        messagebox.showerror("Erro", "Configuração de repositório cancelada.")
        return {}

    config = {"usuario": usuario, "repositorio": repositorio}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    return config

def montar_url_pr(origem, destino):
    cfg = get_repo_config()
    if not cfg:
        return None
    return f"https://github.com/{cfg['usuario']}/{cfg['repositorio']}/compare/{destino}...{origem}"


def montar_url_pr(origem, destino):
    cfg = get_repo_config()
    if not cfg:
        return None
    return f"https://github.com/{cfg['usuario']}/{cfg['repositorio']}/compare/{destino}...{origem}"


def log(mensagem):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {mensagem}\n")


def get_logs():
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return f.read()
    return ""


def clear_logs():
    if os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("")


def run_command(command):
    if not repo_path:
        return "", "Repositório não selecionado."

    try:
        log(f"Executando: {command}")
        result = subprocess.run(command, shell=True, cwd=repo_path, capture_output=True, text=True, check=True)
        if result.stdout:
            log(f"Saída: {result.stdout.strip()}")
        return result.stdout.strip(), ""
    except subprocess.CalledProcessError as e:
        log(f"Erro: {e.stderr.strip()}")
        return "", e.stderr.strip()


def has_changes():
    stdout, _ = run_command("git status --porcelain")
    return bool(stdout.strip())
