import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from utils import set_repo_path, get_repo_path, has_changes, get_logs
from git_operations import criar_branch, fazer_commit, push, atualizar_branch_principal

def iniciar_interface():
    janela = tk.Tk()
    janela.title("Automacao Git com Tkinter")
    janela.geometry("600x500")

    repo_var = tk.StringVar()
    log_output = tk.Text(janela, height=15)

    def atualizar_logs():
        log_output.delete("1.0", tk.END)
        log_output.insert(tk.END, get_logs())

    def selecionar_repositorio():
        path = filedialog.askdirectory()
        if path:
            set_repo_path(path)
            repo_var.set(path)
            atualizar_logs()

    def acao_criar_branch():
        nome = simpledialog.askstring("Nome da Branch", "Digite o nome da nova branch:")
        if not nome:
            return
        sucesso, msg = criar_branch(nome)
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showerror("Erro", msg)
        atualizar_logs()

    def acao_commit():
        if not get_repo_path():
            messagebox.showerror("Erro", "Repositório não selecionado.")
            return
        if not has_changes():
            messagebox.showwarning("Aviso", "Nenhuma alteração para commit.")
            return
        msg = simpledialog.askstring("Mensagem do Commit", "Digite a mensagem do commit:")
        if msg:
            _, output = fazer_commit(msg)
            messagebox.showinfo("Sucesso", output)
        atualizar_logs()

    def acao_commit_push():
        acao_commit()
        _, output = push()
        messagebox.showinfo("Push", output)
        atualizar_logs()

    def acao_atualizar_branch_principal():
        sucesso, msg = atualizar_branch_principal()
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showerror("Erro", msg)
        atualizar_logs()

    # Interface
    tk.Label(janela, text="Repositório Git:").pack(pady=5)
    tk.Entry(janela, textvariable=repo_var, width=60, state="readonly").pack(padx=10)
    tk.Button(janela, text="Selecionar Repositório", command=selecionar_repositorio).pack(pady=10)

    tk.Button(janela, text="Atualizar Branch Principal", command=acao_atualizar_branch_principal, width=40).pack(pady=5)
    tk.Button(janela, text="Criar Branch (feature/)", command=acao_criar_branch, width=40).pack(pady=5)
    tk.Button(janela, text="Fazer Commit", command=acao_commit, width=40).pack(pady=5)
    tk.Button(janela, text="Commit + Push", command=acao_commit_push, width=40).pack(pady=5)
    tk.Button(janela, text="Sair", command=janela.quit, width=40).pack(pady=20)

    tk.Label(janela, text="Logs:").pack()
    log_output.pack(padx=10, fill="both", expand=True)

    atualizar_logs()
    janela.mainloop()
