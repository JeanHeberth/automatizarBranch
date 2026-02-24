import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Importação de serviços desacoplados
from services.branch_service import list_branches, update_branch, create_branch, checkout_branch, list_remote_branches, \
    safe_checkout
from services.commit_service import commit_changes, commit_and_push
from services.delete_service import delete_remote_branch, delete_local_branch, delete_all_local_branches
from services.rollback_service import rollback_commit, rollback_changes
from services.pr_service import create_pr, merge_pr
from core.git_operations import GitCommandError, get_current_branch, get_default_main_branch
from utils.worker_thread import run_in_thread
from core.logger_config import setup_logging, get_ui_handler


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configurar logging
        setup_logging()
        self.title("🚀 Automação Git com Tkinter")
        self.resizable(True, True)
        self.minsize(800, 850)
        self.configure(bg="#f7f8fa", padx=5, pady=5)
        self.repo_path = None
        self.is_loading = False
        self._setup_theme()
        self._build_ui()

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
        ttk.Label(self, text="Automação de Branches 💡", font=("Segoe UI Semibold", 16)).pack(pady=(0, 2))
        ttk.Label(self, text="Gerencie branches, commits e PRs de forma visual e simples.", font=("Segoe UI", 10)).pack(
            pady=(0, 15))

        ttk.Label(self, text="📁 Repositório Git:", font=("Segoe UI", 12, "bold")).pack(pady=(5, 0))

        self.repo_entry = ttk.Entry(self, width=50, state="readonly")
        self.repo_entry.pack(pady=5)

        ttk.Button(self, text="Selecionar Repositório", width=50, command=self.on_select_repo).pack(pady=(5, 0))

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        buttons = [
            ("🔄 Atualizar Branch", self.on_atualizar_branch),
            ("↩️ Rollback de Alterações", self.on_realizar_rollback_de_alteracoes),
            ("↩️ Rollback de Commit", self.on_realizar_rollback),
            ("🌿 Checkout de Branch", self.on_checkout_branch),
            ("🌱 Criar Branch", self.on_criar_branch),
            ("💬 Fazer Commit", self.on_commit),
            ("💾 Commit + Push", self.on_commit_push),
            ("🔗 Criar Pull Request", self.on_criar_pr),
            ("✅ Merge Pull Request", self.on_merge_pr),
            ("🧹 Deletar Todas Locais", self.on_deletar_todas_locais),
            ("🗑️ Deletar Branch Local", self.on_deletar_branch_local),
            ("🚮 Deletar Branch Remota", self.on_deletar_branch_remota),
            ("❌ Sair", self.destroy),
        ]

        for text, cmd in buttons:
            ttk.Button(button_frame, text=text, width=50, command=cmd).pack(pady=4, fill="x")

        ttk.Label(self,
                  text="🧾 Logs de Execução:",
                  font=("Segoe UI", 12, "bold"),
                  anchor="center",
                  justify="center").pack(pady=(15, 5))

        self.log_text = tk.Text(
            self,
            height=10,
            width=80,
            state="disabled",
            bg="#F3F6FA",
            fg="#2E3440",
            relief="flat",
            font=("Segoe UI", 12, "bold")
        )
        self.log_text.pack(pady=(0, 5))

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
