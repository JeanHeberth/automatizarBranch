import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Importação de serviços desacoplados
from services.branch_service import list_branches, update_branch, create_branch, checkout_branch, list_remote_branches, \
    safe_checkout
from services.commit_service import commit_changes, commit_and_push
from services.delete_service import delete_remote_branch, delete_local_branch, delete_all_local_branches, delete_all_remote_branches
from services.rollback_service import rollback_commit, rollback_changes
from services.pr_service import create_pr, merge_pr
from services.stash_service import stash_save, stash_list, stash_apply, stash_pop, stash_drop, stash_clear
from core.git_operations import GitCommandError, get_current_branch, get_default_main_branch
from utils.worker_thread import run_in_thread
from core.logger_config import setup_logging, get_ui_handler


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configurar logging
        setup_logging()
        self.title("🚀 Automação Git com Tkinter")
        self.configure(bg="#f7f8fa")
        self.repo_path = None
        self.is_loading = False
        self._setup_theme()
        self._build_ui()
        # Tornar janela responsiva e maximizar ao abrir
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Definir tamanho mínimo adaptativo (ex: 14" notebook ~ 1366x768)
        min_w = min(1000, int(screen_width * 0.95))
        min_h = min(700, int(screen_height * 0.92))
        self.minsize(min_w, min_h)
        self.geometry(f"{min_w}x{min_h}")
        self.resizable(True, True)
        # Maximizar se tela for grande
        if screen_width > 1400:
            self.state('zoomed')

    # =====================================================
    # CONFIGURAÇÃO VISUAL
    # =====================================================
    def _setup_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_main = "#F9FAFB"
        bg_button = "#D7E3F4"
        bg_hover = "#C7D8EE"
        fg_text = "#2E3440"
        border = "#C5CED8"

        style.configure(".", background=bg_main, foreground=fg_text, font=("Segoe UI", 10))
        style.configure("TFrame", background=bg_main)
        style.configure("TLabel", background=bg_main, foreground=fg_text)
        style.configure("TButton", background=bg_button, borderwidth=1, focusthickness=3, padding=6)
        style.map("TButton", background=[("active", bg_hover)])
        style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=border)

    # =====================================================
    # INTERFACE PRINCIPAL
    # =====================================================
    def _build_ui(self):
        # Frame principal centralizado
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Cabeçalho destacado
        header = ttk.Label(main_frame, text="Automação de Branches 🚀", font=("Segoe UI Semibold", 22), anchor="center")
        header.pack(pady=(0, 8))
        subheader = ttk.Label(main_frame, text="Gerencie branches, commits, PRs e mais de forma visual e simples.", font=("Segoe UI", 12), anchor="center")
        subheader.pack(pady=(0, 18))

        # Área do repositório
        repo_frame = ttk.Frame(main_frame)
        repo_frame.pack(fill="x", pady=(0, 18))
        ttk.Label(repo_frame, text="📁 Repositório Git:", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.repo_entry = ttk.Entry(repo_frame, width=50, state="readonly")
        self.repo_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
        ttk.Button(repo_frame, text="Selecionar Repositório", command=self.on_select_repo).pack(side="left", padx=(12, 0))

        # Frame de botões agrupados por categoria
        button_area = ttk.Frame(main_frame)
        button_area.pack(fill="x", pady=(0, 18))

        def add_group(title, buttons, btn_width=22):
            group = ttk.LabelFrame(button_area, text=title, padding=(12, 8))
            group.pack(side="left", padx=10, fill="y", expand=True, anchor="n")
            for text, cmd in buttons:
                ttk.Button(group, text=text, width=btn_width, command=cmd).pack(pady=4, fill="x")

        add_group("Branch", [
            ("🔄 Atualizar Branch", self.on_atualizar_branch),
            ("🌿 Checkout de Branch", self.on_checkout_branch),
            ("🌱 Criar Branch", self.on_criar_branch),
        ], btn_width=22)
        add_group("Commit", [
            ("💬 Fazer Commit", self.on_commit),
            ("💾 Commit + Push", self.on_commit_push),
            ("↩️ Rollback de Alterações", self.on_realizar_rollback_de_alteracoes),
            ("↩️ Rollback de Commit", self.on_realizar_rollback),
        ], btn_width=22)
        add_group("Pull Request", [
            ("🔗 Criar Pull Request", self.on_criar_pr),
            ("✅ Merge Pull Request", self.on_merge_pr),
        ], btn_width=22)
        add_group("Stash", [
            ("💾 Salvar Stash", self.on_salvar_stash),
            ("📋 Ver Stashes", self.on_ver_stashes),
            ("♻️ Aplicar Stash", self.on_aplicar_stash),
            ("🗑️ Limpar Stashes", self.on_limpar_stashes),
        ], btn_width=22)
        add_group("Deleção", [
            ("🧹 Deletar Todas as Branches Locais (exceto protegidas)", self.on_deletar_todas_locais),
            ("🗑️ Deletar Branch Local Selecionada", self.on_deletar_branch_local),
            ("🧹 Deletar Todas as Branches Remotas (exceto protegidas)", self.on_deletar_todas_remotas),
            ("🚮 Deletar Branch Remota Selecionada", self.on_deletar_branch_remota),
            ("❌ Sair do Sistema", self.destroy),
        ], btn_width=60)

        # Área de logs separada visualmente
        logs_label = ttk.Label(main_frame, text="🧾 Logs de Execução:", font=("Segoe UI", 13, "bold"), anchor="w")
        logs_label.pack(pady=(18, 4), anchor="w")
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill="both", expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical")
        log_scrollbar.pack(side="right", fill="y")
        self.log_text = tk.Text(
            log_frame,
            height=12,
            width=100,
            state="disabled",
            bg="#F3F6FA",
            fg="#2E3440",
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            yscrollcommand=log_scrollbar.set,
            wrap="word"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.config(command=self.log_text.yview)

    # =====================================================
    # UTILITÁRIOS
    # =====================================================
    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[LOG] {text}\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def _run_async(self, func, args=(), on_success=None, on_error=None):
        """Executa função em thread para não congelar UI."""
        def on_success_wrapper(result):
            self.is_loading = False
            if on_success:
                on_success(result)

        def on_error_wrapper(error):
            self.is_loading = False
            if on_error:
                on_error(error)

        def on_finally():
            # Atualizar UI após conclusão
            self.update_idletasks()

        self.is_loading = True
        run_in_thread(
            func,
            args=args,
            on_success=on_success_wrapper,
            on_error=on_error_wrapper,
            on_finally=on_finally
        )

    def on_select_repo(self):
        repo = filedialog.askdirectory(title="Selecione o repositório Git")
        if repo:
            # Validar se é um repositório Git
            import os
            if not os.path.isdir(os.path.join(repo, ".git")):
                return messagebox.showerror("Erro", "Pasta selecionada não é um repositório Git válido.\nCertifique-se de que contém a pasta '.git'.")

            self.repo_path = repo
            self.repo_entry.config(state="normal")
            self.repo_entry.delete(0, "end")
            self.repo_entry.insert(0, repo)
            self.repo_entry.config(state="readonly")
            self.log(f"Repositório selecionado: {repo}")

    # =====================================================
    # POPUP PADRÃO
    # =====================================================
    def _popup(self, title, label_text, callback, entry=False, combo_values=None):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("420x200")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text=label_text, font=("Segoe UI", 10)).pack(pady=(10, 5))
        var = tk.StringVar()
        widget = None

        if combo_values:
            widget = ttk.Combobox(popup, textvariable=var, values=combo_values, state="readonly", width=40)
            var.set(combo_values[0])
        elif entry:
            widget = ttk.Entry(popup, textvariable=var, width=45)

        if widget:
            widget.pack(pady=10)

        def confirmar():
            value = var.get().strip()
            # Validação de entrada
            if not value:
                return messagebox.showwarning("Aviso", "Campo não pode estar vazio!")
            popup.destroy()
            callback(value)

        ttk.Button(popup, text="Confirmar", command=confirmar).pack(pady=10)

    # =====================================================
    # OPERAÇÕES GIT VIA SERVICES
    # =====================================================
    def on_atualizar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        try:
            branches = list_branches(self.repo_path)
        except Exception as e:
            return messagebox.showerror("Erro", str(e))

        def atualizar(branch):
            def execute():
                return update_branch(self.repo_path, branch)

            def on_success(msg):
                messagebox.showinfo("Sucesso", msg)
                self.log(msg)

            def on_error(error):
                messagebox.showerror("Erro", str(error))
                self.log(f"Erro ao atualizar branch: {error}")

            self._run_async(execute, on_success=on_success, on_error=on_error)

        self._popup("Atualizar Branch", "Selecione uma branch:", atualizar, combo_values=branches)

    def on_checkout_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        try:
            branches = list_branches(self.repo_path)
            self._popup("Checkout", "Selecione uma branch:", self._checkout_action, combo_values=branches)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _checkout_action(self, branch):
        try:
            result = safe_checkout(self.repo_path, branch)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_criar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        self._popup("Criar Branch", "Digite o nome da nova branch:", self._criar_branch_action, entry=True)

    def _criar_branch_action(self, name):
        try:
            result = create_branch(self.repo_path, name)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_commit(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        self._popup("Commit", "Mensagem do commit:", self._commit_action, entry=True)

    def _commit_action(self, msg):
        try:
            result = commit_changes(self.repo_path, msg)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_commit_push(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        self._popup("Commit + Push", "Mensagem do commit:", self._commit_push_action, entry=True)

    def _commit_push_action(self, msg):
        def execute():
            return commit_and_push(self.repo_path, msg)

        def on_success(result):
            messagebox.showinfo("Sucesso", result)
            self.log(result)

        def on_error(error):
            messagebox.showerror("Erro", str(error))
            self.log(str(error))

        self._run_async(execute, on_success=on_success, on_error=on_error)

    def on_realizar_rollback(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        resposta = messagebox.askyesno("Rollback", "Deseja realizar rollback leve (Sim) ou completo (Não)?")
        try:
            result = rollback_commit(self.repo_path, soft=resposta)
            messagebox.showinfo("Rollback", result)
            self.log(result)
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_realizar_rollback_de_alteracoes(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        confirmar = messagebox.askyesno(
            "Desfazer alterações",
            "Deseja descartar todas as alterações locais não commitadas?\n⚠️ Essa ação não pode ser desfeita."
        )
        if not confirmar:
            return
        try:
            result = rollback_changes(self.repo_path)
            messagebox.showinfo("Rollback", result)
            self.log(result)
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

        # =====================================================
        # CRIAR PULL REQUEST
        # =====================================================

    def on_criar_pr(self):
        if not self.repo_path:
            return messagebox.showwarning("Repositório", "Selecione um repositório primeiro.")

        branches = list_branches(self.repo_path)

        popup = tk.Toplevel(self)
        popup.title("Criar Pull Request")
        popup.geometry("420x280")
        popup.configure(bg="#F9FAFB")

        ttk.Label(popup, text="Branch Base (destino do PR):").pack(pady=5)
        default_base = get_default_main_branch(self.repo_path)
        base_var = tk.StringVar(value=default_base)
        base_combo = ttk.Combobox(popup, textvariable=base_var, values=branches, state="readonly", width=40)
        base_combo.pack()

        ttk.Label(popup, text="Branch Compare (origem):").pack(pady=5)
        compare_var = tk.StringVar(value=get_current_branch(self.repo_path))
        compare_combo = ttk.Combobox(popup, textvariable=compare_var, values=branches, state="readonly", width=40)
        compare_combo.pack()

        ttk.Label(popup, text="Título do PR:").pack(pady=5)
        title_var = tk.StringVar(value=f"Merge {compare_var.get()} → {base_var.get()}")
        entry = ttk.Entry(popup, textvariable=title_var, width=45)
        entry.pack()

        def atualizar_titulo(*_):
            title_var.set(f"Merge {compare_var.get()} → {base_var.get()}")

        base_combo.bind("<<ComboboxSelected>>", atualizar_titulo)
        compare_combo.bind("<<ComboboxSelected>>", atualizar_titulo)

        def criar_pr_action():
            def execute():
                return create_pr(self.repo_path, base_var.get(), compare_var.get(), title_var.get())

            def on_success(msg):
                messagebox.showinfo("Sucesso", msg)
                self.log(msg)
                popup.destroy()

            def on_error(error):
                messagebox.showerror("Erro", str(error))
                self.log(f"Erro ao criar PR: {error}")

            self._run_async(execute, on_success=on_success, on_error=on_error)

        ttk.Button(popup, text="Criar Pull Request", command=criar_pr_action).pack(pady=15)

    # =====================================================
    # MERGE PULL REQUEST
    # =====================================================
    def on_merge_pr(self):
        if not self.repo_path:
            return messagebox.showwarning("Repositório", "Selecione um repositório primeiro.")
        popup = tk.Toplevel(self)
        popup.title("✅ Merge Pull Request")
        popup.geometry("420x220")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Número do Pull Request (PR):").pack(pady=(20, 5))
        pr_var = tk.StringVar()
        ttk.Entry(popup, textvariable=pr_var, width=40).pack(pady=(0, 10))

        def confirmar():
            pr_number = pr_var.get().strip()
            if not pr_number.isdigit():
                return messagebox.showwarning("Aviso", "Informe um número de PR válido.")

            def execute():
                return merge_pr(self.repo_path, int(pr_number))

            def on_success(msg):
                messagebox.showinfo("Merge PR", msg)
                self.log(msg)
                popup.destroy()

            def on_error(error):
                messagebox.showerror("Erro no Merge PR", str(error))
                self.log(f"Erro ao mesclar PR: {error}")

            self._run_async(execute, on_success=on_success, on_error=on_error)

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=20)

        button_width = 15

        ttk.Button(
            button_frame,
            text="Fazer Merge do PR",
            command=confirmar,
            width=button_width
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=popup.destroy,
            width=button_width
        ).grid(row=0, column=1, padx=5)

    # =====================================================
    # DELEÇÃO DE BRANCHES
    # =====================================================
    def on_deletar_todas_locais(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        if not messagebox.askyesno("Confirmação", "Deseja deletar TODAS as branches locais (exceto protegidas)?"):
            return
        try:
            result = delete_all_local_branches(self.repo_path)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_deletar_branch_local(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        try:
            locals_ = list_branches(self.repo_path)
            self._popup("Deletar Branch Local", "Selecione uma branch:", self._del_local_action, combo_values=locals_)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _del_local_action(self, branch):
        try:
            result = delete_local_branch(self.repo_path, branch)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_deletar_branch_remota(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        try:
            remotas = list_remote_branches(self.repo_path)
            self._popup("Deletar Branch Remota", "Selecione uma branch remota:", self._del_remote_action,
                        combo_values=remotas)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _del_remote_action(self, branch):
        try:
            result = delete_remote_branch(self.repo_path, branch)
            messagebox.showinfo("Sucesso", result)
            self.log(result)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_deletar_todas_remotas(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        if not messagebox.askyesno("Confirmação", "Deseja deletar TODAS as branches remotas (exceto protegidas: main, master, develop)?"):
            return

        def execute():
            return delete_all_remote_branches(self.repo_path)

        def on_success(result):
            messagebox.showinfo("Sucesso", result)
            self.log(result)

        def on_error(error):
            messagebox.showerror("Erro", str(error))
            self.log(str(error))

        self._run_async(execute, on_success=on_success, on_error=on_error)

    # =====================================================
    # OPERAÇÕES DE STASH
    # =====================================================
    def on_salvar_stash(self):
        """Salva as alterações atuais em um stash."""
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        popup = tk.Toplevel(self)
        popup.title("💾 Salvar Stash")
        popup.geometry("420x180")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Mensagem do Stash (opcional):").pack(pady=(20, 5))
        msg_var = tk.StringVar()
        ttk.Entry(popup, textvariable=msg_var, width=40).pack(pady=(0, 10))

        def confirmar():
            message = msg_var.get().strip()
            popup.destroy()

            def execute():
                return stash_save(self.repo_path, message if message else None)

            def on_success(result):
                messagebox.showinfo("Stash Salvo", result)
                self.log(result)

            def on_error(error):
                messagebox.showerror("Erro", str(error))
                self.log(str(error))

            self._run_async(execute, on_success=on_success, on_error=on_error)

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Salvar", command=confirmar, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=popup.destroy, width=15).grid(row=0, column=1, padx=5)

    def on_ver_stashes(self):
        """Lista todos os stashes salvos."""
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        try:
            stashes = stash_list(self.repo_path)

            if not stashes:
                messagebox.showinfo("Stashes", "📋 Nenhum stash encontrado.")
                self.log("Nenhum stash encontrado.")
                return

            # Criar popup com lista de stashes
            popup = tk.Toplevel(self)
            popup.title("📋 Lista de Stashes")
            popup.geometry("600x400")
            popup.configure(bg="#F9FAFB")

            ttk.Label(popup, text="Stashes Salvos:", font=("Segoe UI", 12, "bold")).pack(pady=10)

            # Frame com scrollbar
            frame = ttk.Frame(popup)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                frame,
                yscrollcommand=scrollbar.set,
                font=("Courier", 10),
                bg="#FFFFFF",
                selectmode="single"
            )
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            for stash in stashes:
                listbox.insert("end", stash)

            button_frame = ttk.Frame(popup)
            button_frame.pack(pady=10)

            def aplicar_selecionado():
                selection = listbox.curselection()
                if not selection:
                    return messagebox.showwarning("Aviso", "Selecione um stash primeiro.")

                stash_text = listbox.get(selection[0])
                stash_ref = stash_text.split(":")[0]

                def execute():
                    return stash_apply(self.repo_path, stash_ref)

                def on_success(result):
                    messagebox.showinfo("Sucesso", result)
                    self.log(result)
                    popup.destroy()

                def on_error(error):
                    messagebox.showerror("Erro", str(error))
                    self.log(str(error))

                self._run_async(execute, on_success=on_success, on_error=on_error)

            def pop_selecionado():
                selection = listbox.curselection()
                if not selection:
                    return messagebox.showwarning("Aviso", "Selecione um stash primeiro.")

                stash_text = listbox.get(selection[0])
                stash_ref = stash_text.split(":")[0]

                def execute():
                    return stash_pop(self.repo_path, stash_ref)

                def on_success(result):
                    messagebox.showinfo("Sucesso", result)
                    self.log(result)
                    popup.destroy()

                def on_error(error):
                    messagebox.showerror("Erro", str(error))
                    self.log(str(error))

                self._run_async(execute, on_success=on_success, on_error=on_error)

            def deletar_selecionado():
                selection = listbox.curselection()
                if not selection:
                    return messagebox.showwarning("Aviso", "Selecione um stash primeiro.")

                stash_text = listbox.get(selection[0])
                stash_ref = stash_text.split(":")[0]

                if not messagebox.askyesno("Confirmar", f"Deseja deletar o stash '{stash_ref}'?"):
                    return

                def execute():
                    return stash_drop(self.repo_path, stash_ref)

                def on_success(result):
                    messagebox.showinfo("Sucesso", result)
                    self.log(result)
                    popup.destroy()

                def on_error(error):
                    messagebox.showerror("Erro", str(error))
                    self.log(str(error))

                self._run_async(execute, on_success=on_success, on_error=on_error)

            ttk.Button(button_frame, text="♻️ Aplicar (manter)", command=aplicar_selecionado, width=20).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="✅ Aplicar + Deletar", command=pop_selecionado, width=20).grid(row=0, column=1, padx=5)
            ttk.Button(button_frame, text="🗑️ Deletar", command=deletar_selecionado, width=20).grid(row=0, column=2, padx=5)
            ttk.Button(button_frame, text="Fechar", command=popup.destroy, width=20).grid(row=1, column=1, pady=10)

            self.log(f"Encontrados {len(stashes)} stash(es).")

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(str(e))

    def on_aplicar_stash(self):
        """Aplica o stash mais recente."""
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        try:
            stashes = stash_list(self.repo_path)
            if not stashes:
                messagebox.showinfo("Stash", "📋 Nenhum stash para aplicar.")
                self.log("Nenhum stash encontrado.")
                return
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        popup = tk.Toplevel(self)
        popup.title("♻️ Aplicar Stash")
        popup.geometry("420x160")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Escolha a operação:", font=("Segoe UI", 11, "bold")).pack(pady=(20, 10))

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=10)

        def aplicar_manter():
            popup.destroy()

            def execute():
                return stash_apply(self.repo_path)

            def on_success(result):
                messagebox.showinfo("Sucesso", result)
                self.log(result)

            def on_error(error):
                messagebox.showerror("Erro", str(error))
                self.log(str(error))

            self._run_async(execute, on_success=on_success, on_error=on_error)

        def aplicar_deletar():
            popup.destroy()

            def execute():
                return stash_pop(self.repo_path)

            def on_success(result):
                messagebox.showinfo("Sucesso", result)
                self.log(result)

            def on_error(error):
                messagebox.showerror("Erro", str(error))
                self.log(str(error))

            self._run_async(execute, on_success=on_success, on_error=on_error)

        ttk.Button(button_frame, text="♻️ Aplicar (manter stash)", command=aplicar_manter, width=25).pack(pady=5)
        ttk.Button(button_frame, text="✅ Aplicar + Deletar stash", command=aplicar_deletar, width=25).pack(pady=5)
        ttk.Button(button_frame, text="Cancelar", command=popup.destroy, width=25).pack(pady=5)

    def on_limpar_stashes(self):
        """Limpa todos os stashes."""
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        if not messagebox.askyesno("Confirmação", "⚠️ Deseja deletar TODOS os stashes?\nEsta ação não pode ser desfeita!"):
            return

        def execute():
            return stash_clear(self.repo_path)

        def on_success(result):
            messagebox.showinfo("Sucesso", result)
            self.log(result)

        def on_error(error):
            messagebox.showerror("Erro", str(error))
            self.log(str(error))

        self._run_async(execute, on_success=on_success, on_error=on_error)

