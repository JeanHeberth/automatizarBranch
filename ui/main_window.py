import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.git_operations import run_git_command, get_current_branch, rollback_last_commit, GitCommandError
from core.pr_operations import create_pull_request


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Automação Git com Tkinter")
        self.geometry("640x770")
        self.configure(bg="#F9FAFB", padx=25, pady=25)
        self.repo_path = None
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

        style.configure(
            ".",
            background=bg_main,
            foreground=fg_text,
            font=("Segoe UI", 10)
        )
        style.configure("TFrame", background=bg_main)
        style.configure("TLabel", background=bg_main, foreground=fg_text)
        style.configure(
            "TButton",
            background=bg_button,
            borderwidth=1,
            focusthickness=3,
            padding=6
        )
        style.map("TButton", background=[("active", bg_hover)])
        style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=border)

    # =====================================================
    # INTERFACE PRINCIPAL
    # =====================================================
    def _build_ui(self):
        ttk.Label(
            self,
            text="Automação de Branches 💡",
            font=("Segoe UI Semibold", 16)
        ).pack(pady=(0, 2))

        ttk.Label(
            self,
            text="Gerencie branches, commits e PRs de forma visual e simples.",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 15))

        ttk.Label(
            self,
            text="📁 Repositório Git:",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(5, 0))

        self.repo_entry = ttk.Entry(self, width=80, state="readonly")
        self.repo_entry.pack(pady=5)

        ttk.Button(
            self,
            text="Selecionar Repositório",
            command=self.on_select_repo
        ).pack(pady=(5, 15), fill="x")

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        buttons = [
            ("🔄 Atualizar Branch", self.on_atualizar_branch),
            ("↩️ Realizar Rollback", self.on_realizar_rollback),
            ("🌿 Checkout de Branch", self.on_checkout_branch),
            ("🌱 Criar Branch", self.on_criar_branch),
            ("💬 Fazer Commit", self.on_commit),
            ("💾 Commit + Push", self.on_commit_push),
            ("🔗 Criar Pull Request", self.on_criar_pr),
            ("🧩 Resolver Conflitos", self.on_resolver_conflitos),
            ("🧹 Deletar Branch (Todas Locais)", self.on_deletar_todas),
            ("🗑️ Deletar Branch Local", self.on_deletar_local),
            ("🚮 Deletar Branch Remota", self.on_deletar_remota),
            ("❌ Sair", self.destroy)
        ]

        for text, cmd in buttons:
            ttk.Button(button_frame, text=text, command=cmd).pack(pady=4, fill="x")

        ttk.Label(
            self,
            text="\n🧾 Logs de Execução:",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(15, 5))

        self.log_text = tk.Text(
            self,
            height=10,
            width=80,
            state="disabled",
            bg="#F3F6FA",
            fg="#2E3440",
            relief="flat"
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

    def on_select_repo(self):
        repo = filedialog.askdirectory(title="Selecione o repositório Git")
        if repo:
            self.repo_path = repo
            self.repo_entry.config(state="normal")
            self.repo_entry.delete(0, "end")
            self.repo_entry.insert(0, repo)
            self.repo_entry.config(state="readonly")
            self.log(f"Repositório selecionado: {repo}")

    # =====================================================
    # OPERAÇÕES GIT
    # =====================================================
    def on_atualizar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        branches = [
            b.replace("*", "").strip()
            for b in run_git_command(self.repo_path, ["branch"]).splitlines()
            if b.strip()
        ]

        def atualizar(branch):
            try:
                run_git_command(self.repo_path, ["checkout", branch])
                run_git_command(self.repo_path, ["pull", "origin", branch])
                messagebox.showinfo("Sucesso", f"✅ Branch '{branch}' atualizada com sucesso.")
                self.log(f"Branch '{branch}' atualizada.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao atualizar branch: {e}")

        self._popup("Atualizar Branch", "Selecione uma branch para atualizar:", atualizar, combo_values=branches)

    def on_checkout_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        branches = [
            b.replace("*", "").strip()
            for b in run_git_command(self.repo_path, ["branch"]).splitlines()
            if b.strip()
        ]

        def checkout(branch):
            try:
                run_git_command(self.repo_path, ["checkout", branch])
                messagebox.showinfo("Sucesso", f"✅ Checkout realizado para '{branch}'.")
                self.log(f"Checkout em {branch}.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao fazer checkout: {e}")

        self._popup("Checkout de Branch", "Escolha uma branch:", checkout, combo_values=branches)

    def on_criar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        def criar(nome):
            if not nome.strip():
                return messagebox.showwarning("Aviso", "Informe o nome da branch.")
            try:
                run_git_command(self.repo_path, ["checkout", "-b", nome])
                messagebox.showinfo("Sucesso", f"🌱 Branch '{nome}' criada com sucesso.")
                self.log(f"Branch criada: {nome}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao criar branch: {e}")

        self._popup("Criar Branch", "Digite o nome da nova branch:", criar, entry=True)

    def on_commit(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        def commit(msg):
            try:
                run_git_command(self.repo_path, ["add", "."])
                run_git_command(self.repo_path, ["commit", "-m", msg])
                messagebox.showinfo("Sucesso", f"✅ Commit realizado: {msg}")
                self.log(f"Commit realizado: {msg}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro no commit: {e}")

        self._popup("Fazer Commit", "Mensagem do commit:", commit, entry=True)

    def on_commit_push(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        def commit_push(msg):
            try:
                branch = get_current_branch(self.repo_path)
                run_git_command(self.repo_path, ["add", "."])
                run_git_command(self.repo_path, ["commit", "-m", msg])
                run_git_command(self.repo_path, ["push", "-u", "origin", branch])
                messagebox.showinfo("Sucesso", f"✅ Commit e Push enviados para 'origin/{branch}'.")
                self.log(f"Commit + push para {branch}.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro no push: {e}")

        self._popup("Commit + Push", "Mensagem do commit:", commit_push, entry=True)

    def on_realizar_rollback(self):
        if not self.repo_path:
            messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
            return

        resposta = messagebox.askyesnocancel(
            "Rollback",
            "Deseja desfazer o último commit?"
        )

        if resposta is None:
            return  # cancelado

        try:
            mode = "soft" if resposta else "hard"
            branch = rollback_last_commit(self.repo_path, mode=mode)
            tipo = "" if mode == "soft" else "completo"
            self._set_status(f"Rollback ({tipo}) concluído na branch {branch}.")
            messagebox.showinfo(title="Rollback concluído", message=f"Rollback {tipo} realizado com sucesso!")
        except GitCommandError as e:
            self._set_status("Erro ao realizar rollback.")
            messagebox.showerror(title="Erro no rollback", message=str(e))

    # =====================================================
    # POPUPS PADRONIZADOS
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
            value = var.get()
            popup.destroy()
            callback(value)

        ttk.Button(popup, text="Confirmar", command=confirmar).pack(pady=10)

    # =====================================================
    # PULL REQUESTS, CONFLITOS E DELEÇÕES
    # =====================================================
    def on_criar_pr(self):
        if not self.repo_path:
            return messagebox.showwarning("Repositório", "Selecione um repositório primeiro.")

        branches = [
            b.replace("*", "").strip()
            for b in run_git_command(self.repo_path, ["branch"]).splitlines()
            if b.strip()
        ]

        popup = tk.Toplevel(self)
        popup.title("Criar Pull Request")
        popup.geometry("420x260")
        popup.configure(bg="#F9FAFB")

        ttk.Label(popup, text="Branch Base (para onde vai o PR):").pack(pady=5)
        base_var = tk.StringVar(value=branches[0])
        base_combo = ttk.Combobox(popup, textvariable=base_var, values=branches, state="readonly", width=40)
        base_combo.pack()

        ttk.Label(popup, text="Branch Compare (de onde vem o PR):").pack(pady=5)
        compare_var = tk.StringVar(value=branches[1] if len(branches) > 1 else "")
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

        def criar_pr():
            try:
                url = create_pull_request(self.repo_path, base_var.get(), title_var.get())
                messagebox.showinfo("Sucesso", f"✅ Pull Request criado!\n{url}")
                self.log(f"Pull Request criado: {url}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao criar PR: {e}")

        ttk.Button(popup, text="Criar Pull Request", command=criar_pr).pack(pady=15)

    def on_resolver_conflitos(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        try:
            run_git_command(self.repo_path, ["merge", "--continue"])
            messagebox.showinfo("Resolver Conflitos", "✅ Merge continuado com sucesso.")
            self.log("Merge continuado com sucesso.")
        except Exception:
            status = run_git_command(self.repo_path, ["status", "--porcelain"])
            conflitos = [line for line in status.splitlines() if line.startswith("UU ")]
            if conflitos:
                msg = "Arquivos em conflito:\n" + "\n".join(f"• {c[3:]}" for c in conflitos)
                messagebox.showwarning("Conflitos Encontrados", msg)
                self.log(msg)
            else:
                messagebox.showinfo("Resolver Conflitos", "Nenhum merge pendente ou conflito encontrado.")
                self.log("Nenhum merge pendente ou conflito encontrado.")

    def on_deletar_todas(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        if not messagebox.askyesno("Confirmação",
                                   "Deseja deletar TODAS as branches locais (exceto main/master/develop)?"):
            return

        raw = run_git_command(self.repo_path, ["branch"]).splitlines()
        locals_ = [b.replace("*", "").strip() for b in raw if b.strip()]
        protegidas = {"main", "master", "develop"}
        deletadas = []

        for br in locals_:
            if br not in protegidas:
                run_git_command(self.repo_path, ["branch", "-D", br])
                deletadas.append(br)

        if deletadas:
            messagebox.showinfo("Sucesso", f"🧹 Branches deletadas: {', '.join(deletadas)}")
            self.log(f"Branches locais removidas: {', '.join(deletadas)}")
        else:
            messagebox.showinfo("Aviso", "Nenhuma branch deletada (todas protegidas).")

    def on_deletar_local(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
        locals_ = [
            b.replace("*", "").strip()
            for b in run_git_command(self.repo_path, ["branch"]).splitlines()
            if b.strip()
        ]
        if not locals_:
            return messagebox.showinfo("Branches", "Nenhuma branch local encontrada.")

        popup = tk.Toplevel(self)
        popup.title("Deletar Branch Local")
        popup.geometry("400x200")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Selecione a branch local:").pack(pady=10)
        var = tk.StringVar(value=locals_[0])
        ttk.Combobox(popup, textvariable=var, values=locals_, state="readonly", width=40).pack(pady=5)

        def _del():
            br = var.get()
            if br in {"main", "master", "develop"}:
                return messagebox.showwarning("Protegida", f"⚠️ '{br}' é protegida e não pode ser deletada.")
            run_git_command(self.repo_path, ["branch", "-D", br])
            messagebox.showinfo("Sucesso", f"🗑️ Branch local '{br}' removida.")
            self.log(f"Branch local deletada: {br}")
            popup.destroy()

        ttk.Button(popup, text="Deletar", command=_del).pack(pady=12)

    def on_deletar_remota(self):
        if not self.repo_path:
            return messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")

        raw = run_git_command(self.repo_path, ["branch", "-r"]).splitlines()
        remotas = [b.strip().replace("origin/", "") for b in raw if "origin/" in b]
        remotas = sorted(set(remotas))

        if not remotas:
            return messagebox.showinfo("Branches", "Nenhuma branch remota encontrada.")

        popup = tk.Toplevel(self)
        popup.title("Deletar Branch Remota")
        popup.geometry("400x200")
        popup.configure(bg="#F9FAFB")
        popup.resizable(False, False)

        ttk.Label(popup, text="Selecione a branch remota:").pack(pady=10)
        var = tk.StringVar(value=remotas[0])
        ttk.Combobox(popup, textvariable=var, values=remotas, state="readonly", width=40).pack(pady=5)

        def _del():
            br = var.get()
            if br in {"main", "master", "develop"}:
                return messagebox.showwarning("Protegida", f"⚠️ '{br}' é protegida e não pode ser deletada.")
            run_git_command(self.repo_path, ["push", "origin", "--delete", br])
            messagebox.showinfo("Sucesso", f"🗑️ Branch remota '{br}' deletada.")
            self.log(f"Branch remota deletada: {br}")
            popup.destroy()

        ttk.Button(popup, text="Deletar", command=_del).pack(pady=12)

    def _set_status(self, text: str, color: str = "#888"):
        """Atualiza o texto da barra de status inferior."""
        if hasattr(self, "lbl_status"):
            self.lbl_status.config(text=text, fg=color)
            self.lbl_status.update_idletasks()
