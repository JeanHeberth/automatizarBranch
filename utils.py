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
    log(f"Executando: {command}")
    result = subprocess.run(command, shell=True, cwd=repo_path, capture_output=True, text=True)
    if result.stdout:
        log(f"Saída: {result.stdout.strip()}")
    if result.stderr:
        log(f"Erro: {result.stderr.strip()}")
    return result.stdout.strip(), result.stderr.strip()

def has_changes():
    stdout, _ = run_command("git status --porcelain")
    return bool(stdout.strip())