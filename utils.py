import subprocess

repo_path = ""

def set_repo_path(path):
    global repo_path
    repo_path = path

def get_repo_path():
    return repo_path

def run_command(command):
    if not repo_path:
        return "", "Repositório não selecionado."
    result = subprocess.run(command, shell=True, cwd=repo_path, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()


def has_changes():
    stdout, _ = run_command("git status --porcelain")
    return bool(stdout.strip())