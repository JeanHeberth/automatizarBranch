#### GUI #######

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Toplevel, ttk

from git_operations import criar_branch, fazer_commit, push, atualizar_branch, listar_branches, fazer_checkout, \
    get_current_branch, deletar_branches_locais, deletar_branch_remota, criar_pull_request, \
    deletar_branch_remota_com_mensagem, merge_pull_request, deletar_branch_local_com_mensagem
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
        # Detectar diferentes tipos de conflitos
        conflitos_merge, _ = run_command("git diff --name-only --diff-filter=U")
        arquivos_conflito = conflitos_merge.splitlines()
        
        # Verificar se há merge em andamento
        merge_head_exists = run_command("test -f .git/MERGE_HEAD")[1] == ""
        
        # Verificar se há rebase em andamento
        rebase_apply_exists = run_command("test -d .git/rebase-apply")[1] == ""
        rebase_merge_exists = run_command("test -d .git/rebase-merge")[1] == ""
        
        # Verificar status geral do repositório
        status_output, _ = run_command("git status --porcelain")
        
        atualizar_logs()
        
        # Determinar o tipo de conflito
        tipo_conflito = "Desconhecido"
        if merge_head_exists:
            tipo_conflito = "Merge"
        elif rebase_apply_exists or rebase_merge_exists:
            tipo_conflito = "Rebase"
        elif arquivos_conflito:
            tipo_conflito = "Conflitos de arquivo"
        
        if not arquivos_conflito and not merge_head_exists and not rebase_apply_exists and not rebase_merge_exists:
            # Verificar se há conflitos não detectados
            cherry_pick_head = run_command("test -f .git/CHERRY_PICK_HEAD")[1] == ""
            if cherry_pick_head:
                tipo_conflito = "Cherry-pick"
            else:
                messagebox.showinfo("Sem conflitos", "Nenhum conflito detectado no repositório.")
                return
        
        popup = Toplevel()
        popup.title(f"Resolver Conflitos - {tipo_conflito}")
        popup.geometry("650x500")
        popup.grab_set()
        
        # Cabeçalho com informações do conflito
        header_frame = tk.Frame(popup)
        header_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(header_frame, text=f"Tipo de conflito: {tipo_conflito}", 
                font=("Arial", 12, "bold")).pack()
        
        if arquivos_conflito:
            tk.Label(header_frame, text=f"Arquivos com conflito: {len(arquivos_conflito)}", 
                    font=("Arial", 10)).pack()
        
        # Frame para lista de arquivos
        if arquivos_conflito:
            tk.Label(popup, text="Arquivos com conflito:").pack(pady=(10, 5))
            
            lista = tk.Listbox(popup, selectmode=tk.MULTIPLE, width=80, height=10)
            for arquivo in arquivos_conflito:
                lista.insert(tk.END, arquivo)
            lista.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Frame para botões de ação
        button_frame = tk.Frame(popup)
        button_frame.pack(pady=10, padx=10, fill=tk.X)
        
        def abrir_selecionados():
            if not arquivos_conflito:
                messagebox.showinfo("Aviso", "Nenhum arquivo com conflito para abrir.")
                return
                
            selecionados = [lista.get(i) for i in lista.curselection()]
            if not selecionados:
                # Se nenhum selecionado, abrir todos
                selecionados = arquivos_conflito
                
            for arquivo in selecionados:
                run_command(f"code {arquivo}")
            log(f"Abrindo arquivos com conflito: {', '.join(selecionados)}")
            messagebox.showinfo("Info", f"Abertos {len(selecionados)} arquivo(s) no VS Code.")
        
        def executar_git_status():
            output, _ = run_command("git status")
            atualizar_logs()
            
            # Criar popup para mostrar status completo
            status_popup = Toplevel(popup)
            status_popup.title("Git Status")
            status_popup.geometry("600x400")
            status_popup.grab_set()
            
            text_widget = tk.Text(status_popup, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, output)
            text_widget.config(state=tk.DISABLED)
            
            tk.Button(status_popup, text="Fechar", command=status_popup.destroy).pack(pady=5)
        
        def abortar_operacao():
            confirm = messagebox.askyesno("Abortar", 
                                        f"Deseja abortar a operação de {tipo_conflito.lower()} em andamento?\n\n"
                                        "Isso desfará todas as alterações não commitadas.")
            if confirm:
                if merge_head_exists:
                    run_command("git merge --abort")
                elif rebase_apply_exists or rebase_merge_exists:
                    run_command("git rebase --abort")
                elif run_command("test -f .git/CHERRY_PICK_HEAD")[1] == "":
                    run_command("git cherry-pick --abort")
                
                atualizar_logs()
                messagebox.showinfo("Abortado", f"Operação de {tipo_conflito.lower()} abortada com sucesso.")
                popup.destroy()
        
        def continuar_operacao():
            if not arquivos_conflito:
                messagebox.showinfo("Aviso", "Não há conflitos para resolver.")
                return
                
            # Verificar se ainda há conflitos
            conflitos_restantes, _ = run_command("git diff --name-only --diff-filter=U")
            if conflitos_restantes.strip():
                messagebox.showwarning("Conflitos pendentes", 
                                     "Ainda há conflitos não resolvidos. Resolva todos os conflitos antes de continuar.")
                return
            
            confirm = messagebox.askyesno("Continuar", 
                                        f"Todos os conflitos foram resolvidos?\n\n"
                                        "Isso executará:\n  git add .\n  git commit (ou continuará a operação)")
            if confirm:
                run_command("git add .")
                
                if merge_head_exists:
                    run_command("git commit --no-edit")
                    messagebox.showinfo("Sucesso", "Merge finalizado com sucesso.")
                elif rebase_apply_exists or rebase_merge_exists:
                    run_command("git rebase --continue")
                    messagebox.showinfo("Sucesso", "Rebase continuado. Verifique se há mais conflitos.")
                elif run_command("test -f .git/CHERRY_PICK_HEAD")[1] == "":
                    run_command("git cherry-pick --continue")
                    messagebox.showinfo("Sucesso", "Cherry-pick continuado.")
                else:
                    run_command("git commit -m 'Resolvendo conflitos'")
                    messagebox.showinfo("Sucesso", "Conflitos resolvidos e commit realizado.")
                
                atualizar_logs()
                popup.destroy()
        
        def finalizar_conflitos_manual():
            mensagem = simpledialog.askstring("Mensagem do Commit", 
                                             "Digite a mensagem do commit:", 
                                             initialvalue="Resolvendo conflitos")
            if not mensagem:
                return
            
            confirm = messagebox.askyesno("Finalizar", 
                                        f"Deseja executar:\n\n  git add .\n  git commit -m '{mensagem}'?")
            if confirm:
                run_command("git add .")
                run_command(f"git commit -m '{mensagem}'")
                atualizar_logs()
                messagebox.showinfo("Sucesso", "Conflitos resolvidos e commit realizado.")
                popup.destroy()
        
        # Botões organizados em linhas
        if arquivos_conflito:
            tk.Button(button_frame, text="Abrir Arquivos no VS Code", 
                     command=abrir_selecionados, width=25).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Ver Git Status", 
                 command=executar_git_status, width=20).pack(side=tk.LEFT, padx=5)
        
        # Segunda linha de botões
        button_frame2 = tk.Frame(popup)
        button_frame2.pack(pady=5, padx=10, fill=tk.X)
        
        tk.Button(button_frame2, text="Continuar Operação", 
                 command=continuar_operacao, width=20, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame2, text="Commit Manual", 
                 command=finalizar_conflitos_manual, width=20, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame2, text="Abortar Operação", 
                 command=abortar_operacao, width=20, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Botão fechar
        tk.Button(popup, text="Fechar", command=popup.destroy, width=15).pack(pady=10)

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
            confirm = messagebox.askyesno("Finalizar",
                                          "Deseja executar:\n\n  git add .\n  git commit -m 'Resolvendo conflitos'?")
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

    def acao_deletar_branch_local():
        resultado = deletar_branches_locais()
        atualizar_logs()
        messagebox.showinfo("Branches Locais", resultado)

    def acao_deletar_branch():
        branches = listar_branches()
        if not branches:
            messagebox.showerror("Erro", "Nenhuma branch encontrada.")
            return

        popup = Toplevel()
        popup.title("Deletar Branch Local")
        popup.geometry("400x150")
        popup.grab_set()

        tk.Label(popup, text="Selecione uma branch local para deletar:").pack(pady=10)

        branch_var = tk.StringVar()
        combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
        combo.pack(pady=5)
        combo.set(branches[0])

        def confirmar():
            branch = branch_var.get()
            if branch:
                sucesso = deletar_branch_local_com_mensagem(branch)
                atualizar_logs()
                if sucesso:
                    # A função já mostra as mensagens de sucesso/erro
                    pass
            popup.destroy()

        tk.Button(popup, text="Deletar", command=confirmar, width=12).pack(pady=15)

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


    def acao_merge_pull_request():
        numero = simpledialog.askstring("Número do PR", "Digite o número do Pull Request para fazer merge:")
        if not numero:
            return
        try:
            numero = int(numero)
        except ValueError:
            messagebox.showerror("Erro", "Número do PR inválido.")
            return

        sucesso, mensagem = merge_pull_request(numero)
        if sucesso:
            messagebox.showinfo("Sucesso", mensagem)
        else:
            messagebox.showerror("Erro", mensagem)


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
        acao_deletar_branch_local,
        acao_deletar_branch_remota,
        acao_merge_pull_request,
        log_output
    )
    janela.mainloop()
