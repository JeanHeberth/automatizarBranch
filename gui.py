#### GUI #######

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Toplevel, ttk
from git_operations import criar_branch, fazer_commit, push, atualizar_branch, listar_branches, fazer_checkout, \
    get_current_branch, deletar_branches_locais, deletar_branch_remota, criar_pull_request, \
    deletar_branch_remota_com_mensagem
from interface_widgets import construir_interface
from utils import set_repo_path, get_repo_path, has_changes, get_logs, clear_logs, run_command, get_repo_config, log


def iniciar_interface():
    clear_logs()
    janela = tk.Tk()
    janela.title("Automacao Git com Tkinter")
    janela.geometry("800x800")

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
            get_repo_config()

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
            sucesso_commit, msg_commit = fazer_commit(msg)
            if sucesso_commit:
               atualizar_logs()
               messagebox.showinfo("Sucesso", msg_commit)
            else:
                messagebox.showerror("Erro ao fazer commit", msg_commit)

    def acao_commit_push():
        mensagem = simpledialog.askstring("Mensagem do Commit", "Digite a mensagem do commit:")
        if mensagem is None or mensagem.strip() == "":
            messagebox.showinfo("Cancelado", "Commit cancelado.")
            return

        sucesso_commit, msg_commit = fazer_commit(mensagem)
        if not sucesso_commit:
            if "nenhuma modificação" in msg_commit.lower():
                messagebox.showinfo("Info", msg_commit)
            else:
                messagebox.showerror("Erro ao fazer commit", msg_commit)
            return

        sucesso_push, msg_push = push()
        if not sucesso_push:
            messagebox.showerror("Erro ao fazer push", msg_push)
            return

        branch = get_current_branch()
        atualizar_logs()
        print(f"Push feito para a branch {branch}: {msg_push}")
        messagebox.showinfo("Sucesso", f"Push feito para a branch {branch}.")




    def acao_atualizar_branch():
        resultado = atualizar_branch()
        if resultado:
            sucesso, msg = resultado
            if sucesso:
                messagebox.showinfo("Atualização", msg)
            else:
                messagebox.showerror("Erro", msg)
    atualizar_logs()

    def acao_resolver_conflitos():
        stdout, _ = run_command("git diff --name-only --diff-filter=U")
        arquivos_conflito = stdout.splitlines()
        atualizar_logs()

        if not arquivos_conflito:
            messagebox.showinfo("Sem conflitos", "Nenhum conflito detectado.")
            return

        popup = Toplevel()
        popup.title("Conflitos detectados")
        popup.geometry("550x400")
        popup.grab_set()

        tk.Label(popup, text="Arquivos com conflito:").pack(pady=(10, 5))

        lista = tk.Listbox(popup, selectmode=tk.MULTIPLE, width=70, height=12)
        for arquivo in arquivos_conflito:
            lista.insert(tk.END, arquivo)
        lista.pack(pady=10)

        def abrir_selecionados():
            selecionados = [lista.get(i) for i in lista.curselection()]
            if not selecionados:
                messagebox.showinfo("Aviso", "Nenhum arquivo selecionado.")
                return
            for arquivo in selecionados:
                run_command(f"code {arquivo}")
            log(f"Abrindo arquivos com conflito: {', '.join(selecionados)}")
            messagebox.showinfo("Info", "Arquivos abertos no VS Code.")
            popup.destroy()

        def executar_git_status():
            output, _ = run_command("git status")
            atualizar_logs()
            messagebox.showinfo("Git Status", output)

        def finalizar_conflitos():
            confirm = messagebox.askyesno("Finalizar", "Deseja executar:\n\n  git add .\n  git commit -m 'Resolvendo conflitos'?")
            if confirm:
                run_command("git add .")
                run_command("git commit -m 'Resolvendo conflitos'")
                atualizar_logs()
                messagebox.showinfo("Sucesso", "Conflitos resolvidos e commit realizado.")
                popup.destroy()

        tk.Button(popup, text="Abrir Selecionados no VS Code", command=abrir_selecionados, width=40).pack(pady=(5, 5))
        tk.Button(popup, text="Executar git status", command=executar_git_status, width=40).pack(pady=5)
        tk.Button(popup, text="Finalizar Conflitos (add + commit)", command=finalizar_conflitos, width=40).pack(pady=5)

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
                sucesso, mensagem = deletar_branch_remota_com_mensagem(branch)
                if sucesso:
                    messagebox.showinfo("Deletada", mensagem)
                else:
                    if "protegida" in mensagem or "não existe" in mensagem:
                        messagebox.showinfo("Aviso", mensagem)
                    else:
                        messagebox.showerror("Erro", mensagem)
            popup.destroy()

        tk.Button(popup, text="Deletar", command=confirmar, width=10).pack(pady=10)

    def acao_deletar_branches_locais():
        resultado = deletar_branches_locais()
        atualizar_logs()
        messagebox.showinfo("Branches Locais", resultado)

    def acao_deletar_branch_remota(branch):
        if branch:
            sucesso, mensagem = deletar_branch_remota(branch)
            atualizar_logs()
            if sucesso:
                messagebox.showinfo("Branch Remota Deletada", mensagem)
            else:
                messagebox.showwarning("Aviso", mensagem)
            return sucesso, mensagem

    def acao_criar_pr():
        branches = listar_branches()
        if len(branches) < 2:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos duas branches para criar um PR.")
            return

        popup = Toplevel()
        popup.title("Criar Pull Request")
        popup.geometry("500x350")
        popup.grab_set()

        tk.Label(popup, text="Selecione a branch BASE (para onde será feito o PR):").pack(pady=(10, 2))
        base_var = tk.StringVar()
        base_combo = ttk.Combobox(popup, textvariable=base_var, values=branches, state="readonly", width=50)
        base_combo.pack(pady=5)
        base_combo.set("main" if "main" in branches else branches[0])

        tk.Label(popup, text="Selecione a branch COMPARE (de onde vem o PR):").pack(pady=(10, 2))
        compare_var = tk.StringVar()
        compare_combo = ttk.Combobox(popup, textvariable=compare_var, values=branches, state="readonly", width=50)
        compare_combo.pack(pady=5)

        from git_operations import get_current_branch
        branch_atual = get_current_branch()
        if branch_atual in branches:
            compare_combo.set(branch_atual)
        else:
            compare_combo.set(branches[-1])

        tk.Label(popup, text="Título do PR:").pack(pady=(10, 2))
        titulo_var = tk.StringVar(value="Novo Pull Request")
        titulo_entry = tk.Entry(popup, textvariable=titulo_var, width=50)
        titulo_entry.pack(pady=5)

        def confirmar():
            origem = compare_var.get()
            destino = base_var.get()
            titulo = titulo_var.get()

            if not origem or not destino:
                messagebox.showerror("Erro", "Selecione as duas branches.")
                return
            if origem == destino:
                messagebox.showerror("Erro", "Branches origem e destino devem ser diferentes.")
                return

            sucesso, msg = criar_pull_request(origem, destino, titulo)
            if sucesso:
                messagebox.showinfo("PR Criado", msg)
            else:
                messagebox.showerror("Erro ao criar PR", msg)

            popup.destroy()

        tk.Button(popup, text="Criar Pull Request", command=confirmar, width=20).pack(pady=15)

    construir_interface(
        janela, repo_var,
        selecionar_repositorio,
        acao_atualizar_branch,
        acao_criar_branch,
        acao_commit,
        acao_commit_push,
        acao_resolver_conflitos,
        acao_checkout_branch,
        acao_deletar_branch,
        acao_criar_pr,
        acao_deletar_branches_locais,
        acao_deletar_branch_remota,
        log_output
    )

    janela.mainloop()
