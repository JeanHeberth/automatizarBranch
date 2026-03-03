import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Importação de serviços desacoplados
from services.branch_service import list_branches, update_branch, create_branch, list_remote_branches, \
    safe_checkout
from services.branch_service import resolve_conflict
from services.commit_service import commit_changes, commit_and_push
from services.delete_service import delete_remote_branch, delete_local_branch, delete_all_local_branches, delete_all_remote_branches
from services.rollback_service import rollback_commit, rollback_changes
from services.pr_service import create_pr, merge_pr
from services.stash_service import stash_save, stash_list, stash_apply, stash_pop, stash_drop, stash_clear
from core.git_operations import GitCommandError, get_current_branch, get_default_main_branch
from utils.worker_thread import run_in_thread
from core.logger_config import setup_logging
from utils.settings import get_theme, set_theme
from utils.settings import get_protected_branches, set_protected_branches, get_default_strategy, set_default_strategy


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
        # Carregar tema salvo nas configurações do usuário
        saved_theme = get_theme()
        if saved_theme:
            self._set_theme(saved_theme)
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

        # Botão de tema no canto superior direito
        theme_btn = ttk.Button(self, text="🌗", width=3, command=self._show_theme_menu)
        theme_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        self._current_theme = "system"

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
        # Botões padrão menores para não ocuparem tanto espaço em notebooks
        style.configure("TButton", background=bg_button, borderwidth=1, focusthickness=3, padding=4, font=("Segoe UI", 9))
        style.map("TButton", background=[("active", bg_hover)])
        # Estilo específico para botões de deleção (maiores e destaque vermelho)
        style.configure("Danger.TButton", background="#E04B4B", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Danger.TButton", background=[("active", "#C73A3A")], foreground=[("active", "#FFFFFF")])
        # Estilo compacto para botões secundários
        style.configure("Small.TButton", background=bg_button, foreground=fg_text, font=("Segoe UI", 9), padding=2)
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
        subheader.pack(pady=(0, 8))

        # Status label visível para confirmações imediatas (ex.: branch criada a partir de X)
        self.status_label = ttk.Label(main_frame, text="", font=("Segoe UI", 10, "bold"), foreground="#2E8B57")
        self.status_label.pack(pady=(0, 10))

        # Área do repositório
        repo_frame = ttk.Frame(main_frame)
        repo_frame.pack(fill="x", pady=(0, 18))
        ttk.Label(repo_frame, text="📁 Repositório Git:", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.repo_entry = ttk.Entry(repo_frame, width=50, state="readonly")
        self.repo_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
        ttk.Button(repo_frame, text="Selecionar Repositório", command=self.on_select_repo).pack(side="left", padx=(12, 0))
        ttk.Button(repo_frame, text="⚙ Configurações", command=self._open_settings).pack(side="left", padx=(8, 0))

        # Frame de botões agrupados por categoria
        button_area = ttk.Frame(main_frame)
        button_area.pack(fill="x", pady=(0, 18))

        def add_group(title, buttons, btn_width=22):
            group = ttk.LabelFrame(button_area, text=title, padding=(12, 8))
            group.pack(side="left", padx=10, fill="y", expand=True, anchor="n")
            for text, cmd in buttons:
                ttk.Button(group, text=text, width=btn_width, command=cmd).pack(pady=4, fill="x")

        # Grupos com botões menores por padrão (para caber em telas menores)
        add_group("Branch", [
            ("🔄 Atualizar Branch", self.on_atualizar_branch),
            ("🔁 Rebase Branch", lambda: self._quick_update(strategy="rebase")),
            ("🔀 Merge Branch", lambda: self._quick_update(strategy="merge")),
            ("🌿 Checkout de Branch", self.on_checkout_branch),
            ("🌱 Criar Branch", self.on_criar_branch),
        ], btn_width=18)
        add_group("Commit", [
            ("💬 Fazer Commit", self.on_commit),
            ("💾 Commit + Push", self.on_commit_push),
            ("↩️ Rollback de Alterações", self.on_realizar_rollback_de_alteracoes),
            ("↩️ Rollback de Commit", self.on_realizar_rollback),
        ], btn_width=18)
        add_group("Pull Request", [
            ("🔗 Criar Pull Request", self.on_criar_pr),
            ("✅ Merge Pull Request", self.on_merge_pr),
        ], btn_width=18)
        add_group("Stash", [
            ("💾 Salvar Stash", self.on_salvar_stash),
            ("📋 Ver Stashes", self.on_ver_stashes),
            ("♻️ Aplicar Stash", self.on_aplicar_stash),
            ("🗑️ Limpar Stashes", self.on_limpar_stashes),
        ], btn_width=18)

        # Grupo Deleção com botões destacados e maiores (independentes dos outros)
        delete_group = ttk.LabelFrame(button_area, text="Deleção", padding=(12, 8))
        delete_group.pack(side="left", padx=10, fill="y", expand=True, anchor="n")
        # Botões de deleção maiores e com estilo Danger.TButton
        ttk.Button(delete_group, text="🧹 Deletar Todas as Branches Locais (exceto protegidas)", command=self.on_deletar_todas_locais, style="Danger.TButton", width=44).pack(pady=6, fill="x")
        ttk.Button(delete_group, text="🗑️ Deletar Branch Local Selecionada", command=self.on_deletar_branch_local, style="Danger.TButton", width=32).pack(pady=6, fill="x")
        ttk.Button(delete_group, text="🧹 Deletar Todas as Branches Remotas (exceto protegidas)", command=self.on_deletar_todas_remotas, style="Danger.TButton", width=44).pack(pady=6, fill="x")
        ttk.Button(delete_group, text="🚮 Deletar Branch Remota Selecionada", command=self.on_deletar_branch_remota, style="Danger.TButton", width=32).pack(pady=6, fill="x")
        ttk.Button(delete_group, text="❌ Sair do Sistema", command=self.destroy, width=18).pack(pady=6, fill="x")

        # Área de logs separada visualmente
        logs_label = ttk.Label(main_frame, text="🧾 Logs de Execução:", font=("Segoe UI", 13, "bold"), anchor="w")
        logs_label.pack(pady=(18, 4), anchor="w")
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill="both", expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical")
        log_scrollbar.pack(side="right", fill="y")
        # Logs: fonte um pouco menor para caber em telas menores, com wrap e scrollbar
        self.log_text = tk.Text(
            log_frame,
            height=12,
            width=100,
            state="disabled",
            bg="#F3F6FA",
            fg="#2E3440",
            relief="flat",
            font=("Segoe UI", 11),
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

        # Popup simplificado: apenas selecionar a branch que será atualizada
        popup = tk.Toplevel(self)
        popup.title("Atualizar Branch")
        popup.geometry("480x160")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Selecione a branch a ser atualizada:").pack(pady=(12, 4))
        branch_var = tk.StringVar(value=branches[0] if branches else "")
        branch_combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
        branch_combo.pack()

        ttk.Label(popup, text="Será usada a strategy padrão definida em Configurações.", font=("Segoe UI", 9)).pack(pady=(8, 4))

        def confirmar():
            selected_branch = branch_var.get().strip()
            selected_base = None
            selected_strategy = get_default_strategy()
            if not selected_branch:
                return messagebox.showwarning("Aviso", "Selecione uma branch para atualizar.")
            self.log(f"Iniciando atualização da branch '{selected_branch}' (strategy={selected_strategy})")
            popup.destroy()

            def execute():
                self.log(f"[thread] Executando update_branch({selected_branch}, strategy={selected_strategy})")
                return update_branch(self.repo_path, selected_branch, base_branch=selected_base, strategy=selected_strategy)

            def on_success(msg):
                messagebox.showinfo("Sucesso", msg)
                self.log(msg)
                try:
                    # Mostrar confirmação visível por alguns segundos
                    self.status_label.config(text=msg)
                    self.after(8000, lambda: self.status_label.config(text=""))
                except Exception:
                    pass

            def on_error(error):
                err_str = str(error)
                # Se houver conflito, oferecer tentativa de resolução automática
                if "Conflito" in err_str or "conflit" in err_str or "Conflict" in err_str:
                    do_preview = messagebox.askyesno("Resolução automática - Preview", "Deseja testar a resolução em modo PREVIEW (não altera o repositório) antes de aplicar?")
                    choice = messagebox.askquestion("Escolher favor", "Escolha 'theirs' para priorizar alterações da base (recomendado) ou 'ours' para priorizar sua branch.\n\nEscolha 'Yes' para 'theirs' ou 'No' para 'ours'.")
                    favor = "theirs" if choice == "yes" else "ours"

                    if do_preview:
                        def execute_resolve_preview():
                            return resolve_conflict(self.repo_path, selected_branch, base_branch=selected_base, favor=favor, strategy=selected_strategy, preview=True, push=False)

                        def on_success_resolve(msg):
                            messagebox.showinfo("Preview concluído", msg)
                            self.log(msg)

                        def on_error_resolve(err):
                            messagebox.showerror("Falha no preview", str(err))
                            self.log(str(err))

                        self._run_async(execute_resolve_preview, on_success=on_success_resolve, on_error=on_error_resolve)
                        return
                    else:
                        do_push = messagebox.askyesno("Aplicar resolução", "Deseja aplicar a resolução automática na branch e DAR PUSH automático ao remoto? (Escolha NÃO para aplicar localmente sem push)")

                        def execute_resolve_apply():
                            return resolve_conflict(self.repo_path, selected_branch, base_branch=selected_base, favor=favor, strategy=selected_strategy, preview=False, push=do_push)

                        def on_success_resolve(msg):
                            messagebox.showinfo("Resolução aplicada", msg)
                            self.log(msg)

                        def on_error_resolve(err):
                            messagebox.showerror("Falha na resolução automática", str(err))
                            self.log(str(err))

                        self._run_async(execute_resolve_apply, on_success=on_success_resolve, on_error=on_error_resolve)
                        return

                messagebox.showerror("Erro ao atualizar branch", err_str)
                self.log(f"Erro ao atualizar branch: {err_str}")
                # Mostrar instruções claras para resolver conflitos
                messagebox.showerror("Erro ao atualizar branch", str(error))
                self.log(f"Erro ao atualizar branch: {error}")

            self._run_async(execute, on_success=on_success, on_error=on_error)

            self._run_async(execute, on_success=on_success, on_error=on_error)

        ttk.Button(popup, text="Atualizar", command=confirmar, width=18).pack(pady=12)

    def _quick_update(self, strategy: str):
        """Abre popup simples para escolher branch/base e executa update_branch com strategy fixa."""
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        try:
            branches = list_branches(self.repo_path)
        except Exception as e:
            return messagebox.showerror("Erro", str(e))

        popup = tk.Toplevel(self)
        popup.title(f"{strategy.capitalize()} Branch")
        popup.geometry("480x220")
        popup.configure(bg="#F9FAFB")

        ttk.Label(popup, text="Branch (origem):").pack(pady=(12, 4))
        branch_var = tk.StringVar(value=branches[0] if branches else "")
        branch_combo = ttk.Combobox(popup, textvariable=branch_var, values=branches, state="readonly", width=50)
        branch_combo.pack()

        try:
            remotes = list_remote_branches(self.repo_path)
        except Exception:
            remotes = []
        base_options = [b for b in ["develop", "main", "master"] if b in remotes]
        if not base_options:
            base_options = remotes[:3] if remotes else ["main"]

        ttk.Label(popup, text="Branch Base (destino):").pack(pady=(12, 4))
        base_var = tk.StringVar(value=base_options[0] if base_options else "main")
        base_combo = ttk.Combobox(popup, textvariable=base_var, values=base_options, state="readonly", width=50)
        base_combo.pack()

        def confirmar_quick():
            b = branch_var.get().strip()
            base = base_var.get().strip() or None
            if not b:
                return messagebox.showwarning("Aviso", "Selecione uma branch.")
            popup.destroy()

            self.log(f"Iniciando {strategy} de '{b}' sobre '{base}'")

            def execute():
                self.log(f"[thread] Executando update_branch({b}, base={base}, strategy={strategy})")
                return update_branch(self.repo_path, b, base_branch=base, strategy=strategy)

            def on_success(msg):
                messagebox.showinfo("Sucesso", msg)
                self.log(msg)
                try:
                    # Mostrar confirmação visível por alguns segundos
                    self.status_label.config(text=msg)
                    self.after(8000, lambda: self.status_label.config(text=""))
                except Exception:
                    pass

            def on_error(error):
                err_str = str(error)
                if "Conflito" in err_str or "conflito" in err_str or "Conflict" in err_str:
                    do_preview = messagebox.askyesno("Resolução automática - Preview", "Deseja testar a resolução em modo PREVIEW (não altera o repositório) antes de aplicar?")
                    choice = messagebox.askquestion("Escolher favor", "Escolha 'theirs' para priorizar alterações da base (recomendado) ou 'ours' para priorizar sua branch.\n\nEscolha 'Yes' para 'theirs' ou 'No' para 'ours'.")
                    favor = "theirs" if choice == "yes" else "ours"

                    if do_preview:
                        def execute_resolve_preview():
                            return resolve_conflict(self.repo_path, b, base_branch=base, favor=favor, strategy=strategy, preview=True, push=False)

                        def on_success_resolve(msg):
                            messagebox.showinfo("Preview concluído", msg)
                            self.log(msg)

                        def on_error_resolve(err):
                            messagebox.showerror("Falha no preview", str(err))
                            self.log(str(err))

                        self._run_async(execute_resolve_preview, on_success=on_success_resolve, on_error=on_error_resolve)
                        return
                    else:
                        do_push = messagebox.askyesno("Aplicar resolução", "Deseja aplicar a resolução automática na branch e DAR PUSH automático ao remoto? (Escolha NÃO para aplicar localmente sem push)")

                        def execute_resolve_apply():
                            return resolve_conflict(self.repo_path, b, base_branch=base, favor=favor, strategy=strategy, preview=False, push=do_push)

                        def on_success_resolve(msg):
                            messagebox.showinfo("Resolução aplicada", msg)
                            self.log(msg)

                        def on_error_resolve(err):
                            messagebox.showerror("Falha na resolução automática", str(err))
                            self.log(str(err))

                        self._run_async(execute_resolve_apply, on_success=on_success_resolve, on_error=on_error_resolve)
                        return

                messagebox.showerror("Erro", err_str)
                self.log(err_str)

            self._run_async(execute, on_success=on_success, on_error=on_error)

        ttk.Button(popup, text=strategy.capitalize(), command=confirmar_quick, width=20).pack(pady=12)

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
        # Custom popup: name + base selection (default main/master)
        try:
            remotes = list_remote_branches(self.repo_path)
        except Exception:
            remotes = []

        # Build base options: prefer main/master, then develop, then other remotes
        base_options = []
        for pref in ["main", "master", "develop"]:
            if pref in remotes and pref not in base_options:
                base_options.append(pref)
        for r in remotes:
            if r not in base_options:
                base_options.append(r)
        if not base_options:
            base_options = ["main", "develop"]

        popup = tk.Toplevel(self)
        popup.title("Criar Branch")
        popup.geometry("520x200")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Nome da nova branch:").pack(pady=(12, 4))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(popup, textvariable=name_var, width=50)
        name_entry.pack()

        ttk.Label(popup, text="Base (a partir de):").pack(pady=(12, 4))
        base_var = tk.StringVar(value=base_options[0])
        base_combo = ttk.Combobox(popup, textvariable=base_var, values=base_options, state="readonly", width=50)
        base_combo.pack()

        def confirmar():
            name = name_var.get().strip()
            base = base_var.get().strip() or None
            if not name:
                return messagebox.showwarning("Aviso", "Informe o nome da nova branch.")
            popup.destroy()

            def execute():
                return create_branch(self.repo_path, name, base_branch=base)

            def on_success(msg):
                messagebox.showinfo("Sucesso", msg)
                self.log(msg)
                try:
                    # Mostrar confirmação visível por alguns segundos
                    self.status_label.config(text=msg)
                    self.after(8000, lambda: self.status_label.config(text=""))
                except Exception:
                    pass

            def on_error(err):
                messagebox.showerror("Erro", str(err))
                self.log(str(err))

            self._run_async(execute, on_success=on_success, on_error=on_error)

        ttk.Button(popup, text="Criar Branch", command=confirmar).pack(pady=14)

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
                err_str = str(error)
                if "mescl" in err_str.lower() or "merge" in err_str.lower() or "conflit" in err_str.lower():
                    if messagebox.askyesno("Conflito no Merge PR", "Conflito detectado ao mesclar PR. Deseja tentar resolução automática priorizando 'theirs' (base) ou 'ours' (PR)?"):
                        # Ask choice
                        choice = messagebox.askquestion("Escolher favor", "Escolha 'theirs' para priorizar a branch base ou 'ours' para priorizar o PR.\n\nEscolha 'Yes' para 'theirs' ou 'No' para 'ours'.")
                        favor = "theirs" if choice == "yes" else "ours"

                        # Usar branch atual and default base from input (we have pr_number only) -> fallback to default base
                        def execute_resolve():
                            # aqui usamos branch atual
                            branch = get_current_branch(self.repo_path)
                            base = get_default_main_branch(self.repo_path)
                            return resolve_conflict(self.repo_path, branch, base_branch=base, favor=favor, strategy=None)

                        def on_success_resolve(msg):
                            messagebox.showinfo("Resolução automática", msg)
                            self.log(msg)

                        def on_error_resolve(err):
                            messagebox.showerror("Falha na resolução automática", str(err))
                            self.log(str(err))

                        self._run_async(execute_resolve, on_success=on_success_resolve, on_error=on_error_resolve)
                        return
                messagebox.showerror("Erro no Merge PR", err_str)
                self.log(f"Erro ao mesclar PR: {err_str}")

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


    def _show_theme_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Claro", command=lambda: self._set_theme("light"))
        menu.add_command(label="Escuro", command=lambda: self._set_theme("dark"))
        menu.add_command(label="Sistema", command=lambda: self._set_theme("system"))
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def _set_theme(self, theme):
        self._current_theme = theme
        style = ttk.Style()
        if theme == "dark":
            style.theme_use("clam")
            # Fundo principal e frames
            style.configure("TFrame", background="#181A20")
            style.configure("TLabel", background="#181A20", foreground="#FFFFFF")
            style.configure("TLabelFrame", background="#181A20", foreground="#FFFFFF")
            # Botões
            style.configure("TButton", background="#23272e", foreground="#FFFFFF", borderwidth=1, focusthickness=3, padding=6)
            # Danger button visible on dark
            style.configure("Danger.TButton", background="#E04B4B", foreground="#FFFFFF")
            style.map("TButton",
                background=[("active", "#31343b")],
                foreground=[("active", "#FFFFFF")]
            )
            # Entradas
            style.configure("TEntry", fieldbackground="#23272e", foreground="#FFFFFF", bordercolor="#31343b")
            # Área de logs
            if hasattr(self, 'log_text'):
                self.log_text.config(bg="#23272e", fg="#FFFFFF", insertbackground="#FFFFFF")
            self.configure(bg="#181A20")
        elif theme == "light":
            style.theme_use("clam")
            style.configure("TFrame", background="#F9FAFB")
            style.configure("TLabel", background="#F9FAFB", foreground="#2E3440")
            style.configure("TLabelFrame", background="#F9FAFB", foreground="#2E3440")
            style.configure("TButton", background="#D7E3F4", foreground="#2E3440")
            style.configure("Danger.TButton", background="#E04B4B", foreground="#FFFFFF")
            style.map("TButton", background=[("active", "#C7D8EE")])
            style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#2E3440")
            if hasattr(self, 'log_text'):
                self.log_text.config(bg="#F3F6FA", fg="#2E3440", insertbackground="#2E3440")
            self.configure(bg="#F9FAFB")
        else:  # sistema
            import platform
            if platform.system() == "Darwin":
                style.theme_use("clam")
                style.configure("TFrame", background="#F9FAFB")
                style.configure("TLabel", background="#F9FAFB", foreground="#2E3440")
                style.configure("TLabelFrame", background="#F9FAFB", foreground="#2E3440")
                style.configure("TButton", background="#D7E3F4", foreground="#2E3440")
                style.configure("Danger.TButton", background="#E04B4B", foreground="#FFFFFF")
                style.map("TButton", background=[("active", "#C7D8EE")])
                style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#2E3440")
                if hasattr(self, 'log_text'):
                    self.log_text.config(bg="#F3F6FA", fg="#2E3440", insertbackground="#2E3440")
                self.configure(bg="#F9FAFB")
            else:
                style.theme_use("clam")
                style.configure("TFrame", background="#F9FAFB")
                style.configure("TLabel", background="#F9FAFB", foreground="#2E3440")
                style.configure("TLabelFrame", background="#F9FAFB", foreground="#2E3440")
                style.configure("TButton", background="#D7E3F4", foreground="#2E3440")
                style.configure("Danger.TButton", background="#E04B4B", foreground="#FFFFFF")
                style.map("TButton", background=[("active", "#C7D8EE")])
                style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#2E3440")
                if hasattr(self, 'log_text'):
                    self.log_text.config(bg="#F3F6FA", fg="#2E3440", insertbackground="#2E3440")
                self.configure(bg="#F9FAFB")


    def _open_settings(self):
        """Abre um dialog para editar branches protegidas e strategy padrão."""
        popup = tk.Toplevel(self)
        popup.title("Configurações")
        popup.geometry("520x280")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Branches protegidas (separadas por vírgula):").pack(pady=(12, 4))
        pb = get_protected_branches()
        pb_var = tk.StringVar(value=", ".join(pb))
        pb_entry = ttk.Entry(popup, textvariable=pb_var, width=60)
        pb_entry.pack()

        ttk.Label(popup, text="Strategy padrão para atualização:").pack(pady=(12, 4))
        ds = get_default_strategy()
        strategy_var = tk.StringVar(value=ds)
        ttk.Radiobutton(popup, text="Rebase (recomendado)", variable=strategy_var, value="rebase").pack()
        ttk.Radiobutton(popup, text="Merge", variable=strategy_var, value="merge").pack()

        def salvar():
            branches_text = pb_var.get().strip()
            branches = [b.strip() for b in branches_text.split(",") if b.strip()]
            if not branches:
                messagebox.showwarning("Aviso", "Ao menos uma branch protegida deve ser informada.")
                return
            try:
                set_protected_branches(branches)
                set_default_strategy(strategy_var.get())
                messagebox.showinfo("Salvo", "Configurações salvas com sucesso.")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        ttk.Button(popup, text="Salvar", command=salvar).pack(pady=12)
