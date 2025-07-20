import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Toplevel, ttk
from utils import set_repo_path, get_repo_path, has_changes, get_logs, clear_logs, run_command
from git_operations import criar_branch, fazer_commit, push, atualizar_branch_principal, listar_branches, fazer_checkout, get_current_branch
from interface_widgets import construir_interface

def iniciar_interface():
    clear_logs()
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
            clear_logs()
            atualizar_logs()

    def acao_criar_branch():
        nome = simpledialog.askstring("Nome da Branch", "Digite o nome da nova branch:")
        if not nome:
            return
        sucesso, msg = criar_branch(nome)
        atualizar_logs()
        if sucesso:
            messagebox.showinfo("Checkout realizado", f"Branch selecionada com sucesso: {nome}")
        else:
            messagebox.showerror("Erro", msg)

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
            atualizar_logs()
            messagebox.showinfo("Sucesso", output)

    def acao_commit_push():
        acao_commit()
        _, output = push()
        atualizar_logs()
        messagebox.showinfo("Push", output)

    def acao_atualizar_branch_principal():
        sucesso, msg = atualizar_branch_principal()
        atualizar_logs()
        if sucesso:
            messagebox.showinfo("Atualização", msg)
        else:
            messagebox.showerror("Erro", msg)

    def acao_resolver_conflitos():
        stdout, _ = run_command("git diff --name-only --diff-filter=U")
        arquivos_conflito = stdout.splitlines()
        atualizar_logs()
        if arquivos_conflito:
            abrir = messagebox.askyesno("Conflitos detectados", f"Foram encontrados {len(arquivos_conflito)} arquivos com conflito. Abrir no VSCode?")
            if abrir:
                for arquivo in arquivos_conflito:
                    run_command(f"code {arquivo}")
            else:
                messagebox.showinfo("Info", "Após resolver os conflitos, execute 'git add' e 'git commit'.")
        else:
            messagebox.showinfo("Sem conflitos", "Nenhum conflito detectado.")

    def acao_checkout_branch():
        branches = listar_branches()
        if not branches:
            messagebox.showerror("Erro", "Nenhuma branch encontrada.")
            return

        popup = Toplevel()
        popup.title("Checkout de Branch")
        popup.geometry("400x150")
        popup.grab_set()

        tk.Label(popup, text="Selecione uma branch para dar checkout:").pack(pady=10)

        branch_var = tk.StringVar()
        combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
        combo.pack(pady=5)
        combo.set(branches[0])

        def confirmar():
            branch_selecionada = branch_var.get()
            if branch_selecionada:
                sucesso, _ = fazer_checkout(branch_selecionada)
                atualizar_logs()
                if sucesso:
                    messagebox.showinfo("Checkout realizado", f"Branch selecionada com sucesso: {branch_selecionada}")
                else:
                    messagebox.showerror("Erro ao trocar de branch", "Erro ao executar o checkout.")
            popup.destroy()

        tk.Button(popup, text="OK", command=confirmar, width=10).pack(pady=10)

    def acao_deletar_branch():
        branches = listar_branches()
        if not branches:
            messagebox.showerror("Erro", "Nenhuma branch encontrada.")
            return

        popup = Toplevel()
        popup.title("Deletar Branch")
        popup.geometry("400x150")
        popup.grab_set()

        tk.Label(popup, text="Selecione uma branch para deletar:").pack(pady=10)

        branch_var = tk.StringVar()
        combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
        combo.pack(pady=5)
        combo.set(branches[0])

        def confirmar():
            branch = branch_var.get()
            if branch:
                if branch == get_current_branch():
                    messagebox.showwarning("Aviso", "Você não pode deletar a branch atual.")
                else:
                    stdout, stderr = run_command(f"git branch -D {branch}")
                    atualizar_logs()
                    if stderr:
                        messagebox.showerror("Erro ao deletar", stderr)
                    else:
                        messagebox.showinfo("Branch Deletada", f"Branch '{branch}' foi deletada com sucesso.")
            popup.destroy()

        tk.Button(popup, text="Deletar", command=confirmar, width=10).pack(pady=10)

    construir_interface(
        janela, repo_var,
        selecionar_repositorio,
        acao_atualizar_branch_principal,
        acao_criar_branch,
        acao_commit,
        acao_commit_push,
        acao_resolver_conflitos,
        acao_checkout_branch,
        acao_deletar_branch,
        log_output
    )

    janela.mainloop()
