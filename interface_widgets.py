def construir_interface(janela, repo_var, selecionar_repositorio, acao_atualizar_branch_principal,
                        acao_criar_branch, acao_commit, acao_commit_push, acao_resolver_conflitos,
                        acao_checkout_branch, acao_deletar_branch, acao_criar_pr,
                        acao_deletar_branch_local, acao_deletar_branch_remota, log_output):
    import tkinter as tk
    tk.Label(janela, text="Repositório Git:").pack(pady=5)
    tk.Entry(janela, textvariable=repo_var, width=60, state="readonly").pack(padx=10)
    tk.Button(janela, text="Selecionar Repositório", command=selecionar_repositorio).pack(pady=10)

    tk.Button(janela, text="Atualizar Branch", command=acao_atualizar_branch_principal, width=40).pack(pady=5)
    tk.Button(janela, text="Checkout de Branch", command=acao_checkout_branch, width=40).pack(pady=5)
    tk.Button(janela, text="Criar Branch (feature/)", command=acao_criar_branch, width=40).pack(pady=5)
    tk.Button(janela, text="Fazer Commit", command=acao_commit, width=40).pack(pady=5)
    tk.Button(janela, text="Commit + Push", command=acao_commit_push, width=40).pack(pady=5)
    tk.Button(janela, text="Criar Pull Request", command=acao_criar_pr, width=40).pack(pady=5)
    tk.Button(janela, text="Resolver Conflitos", command=acao_resolver_conflitos, width=40).pack(pady=5)
    tk.Button(janela, text="Deletar Branch", command=acao_deletar_branch, width=40).pack(pady=5)
    tk.Button(janela, text="Deletar Branch Local", command=acao_deletar_branch_local, width=40).pack(pady=5)
    tk.Button(janela, text="Deletar Branch Remota", command=lambda: criar_toplevel_deletar_branch_remota(acao_deletar_branch_remota), width=40).pack(pady=5)

    tk.Button(janela, text="Sair", command=janela.quit, width=40).pack(pady=20)

    log_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

def criar_toplevel_deletar_branch_remota(callback):
    import tkinter as tk
    from tkinter import Toplevel, ttk, messagebox
    from git_operations import listar_branches

    popup = Toplevel()
    popup.title("Deletar Branch Remota")
    popup.geometry("400x180")
    popup.grab_set()

    branches = listar_branches()
    if not branches:
        messagebox.showerror("Erro", "Nenhuma branch encontrada.")
        popup.destroy()
        return

    tk.Label(popup, text="Selecione a branch remota para deletar:").pack(pady=10)

    branch_var = tk.StringVar()
    combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
    combo.pack(pady=5)
    combo.set(branches[0])

    def confirmar():
        branch = branch_var.get()
        sucesso, msg = callback(branch)
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showwarning("Aviso", msg)
        popup.destroy()

    tk.Button(popup, text="Deletar", command=confirmar, width=12).pack(pady=15)
