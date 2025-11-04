import subprocess

def run_git_command(repo_path, command_list):
    """Executa comandos git e retorna saída limpa."""
    result = subprocess.run(
        ["git", "-C", repo_path] + command_list,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

def get_current_branch(repo_path):
    """Retorna o nome da branch atual."""
    return run_git_command(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
