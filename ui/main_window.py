import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.git_operations import run_git_command
from core.pr_operations import create_pull_request
from core.git_operations import get_current_branch
import os


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Automação Git com Tkinter")
        self.geometry("620x750")
        self.configure(padx=20, pady=20)
        self.repo_path = None
        self._build_ui()

    # ----------------------------------------------------
    # INTERFACE
    # ----------------------------------------------------
    def _build_ui(self):
        ttk.Label(self, text="Repositório Git:", font=("Segoe UI", 10)).pack(pady=(5, 0))
        self.repo_entry = ttk.Entry(self, width=80, state="readonly")
        self.repo_entry.pack(pady=5)

        ttk.Button(self, text="Selecionar Repositório", command=self.on_select_repo).pack(pady=5)

        buttons = [
            ("Atualizar Branch", self.on_atualizar_branch),
            ("Checkout de Branch", self.on_checkout_branch),
            ("Criar Branch", self.on_criar_branch),
            ("Fazer Commit", self.on_commit),
            ("Commit + Push", self.on_commit_push),
            ("Criar Pull Request", self.on_criar_pr),
            ("Resolver Conflitos", self.on_resolver_conflitos),
            ("Deletar Branch", self.on_deletar_todas),
            ("Deletar Branch Local", self.on_deletar_local),
            ("Deletar Branch Remota", self.on_deletar_remota),
            ("Sair", self.destroy)
        ]

        for text, cmd in buttons:
            ttk.Button(self, text=text, command=cmd).pack(pady=4, fill="x")

        ttk.Label(self, text="\nLogs de Execução:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        self.log_text = tk.Text(self, height=10, width=80, state="disabled", bg="#f7f7f7")
        self.log_text.pack()

    # ----------------------------------------------------
    # FUNÇÕES GIT
    # ----------------------------------------------------
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

    def on_atualizar_branch(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        branches_output = run_git_command(self.repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in branches_output if b.strip()]

        popup = tk.Toplevel(self)
        popup.title("Atualizar Branch")
        popup.geometry("400x200")

        ttk.Label(popup, text="Selecione uma branch para atualizar:").pack(pady=10)
        var = tk.StringVar(value=branches[0])
        combo = ttk.Combobox(popup, textvariable=var, values=branches, state="readonly", width=40)
        combo.pack(pady=5)

        def atualizar():
            branch = var.get()
            try:
                run_git_command(self.repo_path, ["checkout", branch])
                run_git_command(self.repo_path, ["pull", "origin", branch])
                messagebox.showinfo("Sucesso", f"✅ Branch '{branch}' atualizada com sucesso.")
                self.log(f"Branch '{branch}' atualizada.")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao atualizar '{branch}': {e}")

        ttk.Button(popup, text="Atualizar", command=atualizar).pack(pady=10)

    def on_checkout_branch(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        branches_output = run_git_command(self.repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in branches_output if b.strip()]

        popup = tk.Toplevel(self)
        popup.title("Checkout de Branch")
        popup.geometry("400x200")

        ttk.Label(popup, text="Escolha uma branch:").pack(pady=10)
        var = tk.StringVar(value=branches[0])
        combo = ttk.Combobox(popup, textvariable=var, values=branches, state="readonly", width=40)
        combo.pack(pady=5)

        def confirmar():
            branch = var.get()
            try:
                run_git_command(self.repo_path, ["checkout", branch])
                messagebox.showinfo("Sucesso", f"✅ Feito checkout para '{branch}'.")
                self.log(f"Checkout realizado: {branch}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao trocar de branch: {e}")

        ttk.Button(popup, text="Confirmar", command=confirmar).pack(pady=10)

    def on_criar_pr(self):
        if not self.repo_path:
            messagebox.showwarning("Repositório", "Selecione um repositório primeiro.")
            return

        branches_output = run_git_command(self.repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in branches_output if b.strip()]

        popup = tk.Toplevel(self)
        popup.title("Criar Pull Request")
        popup.geometry("420x260")

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

        ttk.Button(popup, text="Criar Pull Request", command=criar_pr).pack(pady=10)

    # ----------------------------------------------------
    # CRIAR BRANCH
    # ----------------------------------------------------
    def on_criar_branch(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        popup = tk.Toplevel(self)
        popup.title("Criar Nova Branch")
        popup.geometry("400x200")

        ttk.Label(popup, text="Digite o nome da nova branch (feature/...):").pack(pady=10)
        nome_var = tk.StringVar()
        entry = ttk.Entry(popup, textvariable=nome_var, width=45)
        entry.pack(pady=5)

        def criar():
            nome = nome_var.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Informe o nome da branch.")
                return
            try:
                run_git_command(self.repo_path, ["checkout", "-b", nome])
                messagebox.showinfo("Sucesso", f"🌱 Branch '{nome}' criada com sucesso.")
                self.log(f"Nova branch criada: {nome}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao criar branch: {e}")

        ttk.Button(popup, text="Criar Branch", command=criar).pack(pady=10)

    # ----------------------------------------------------
    # COMMIT SIMPLES
    # ----------------------------------------------------
    def on_commit(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        popup = tk.Toplevel(self)
        popup.title("Fazer Commit")
        popup.geometry("400x200")

        ttk.Label(popup, text="Mensagem do commit:").pack(pady=10)
        msg_var = tk.StringVar()
        entry = ttk.Entry(popup, textvariable=msg_var, width=45)
        entry.pack(pady=5)

        def commit():
            msg = msg_var.get().strip()
            if not msg:
                messagebox.showwarning("Aviso", "Informe uma mensagem de commit.")
                return
            try:
                run_git_command(self.repo_path, ["add", "."])
                run_git_command(self.repo_path, ["commit", "-m", msg])
                messagebox.showinfo("Sucesso", f"✅ Commit realizado: {msg}")
                self.log(f"Commit realizado: {msg}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao realizar commit: {e}")

        ttk.Button(popup, text="Confirmar Commit", command=commit).pack(pady=10)

    # ----------------------------------------------------
    # COMMIT + PUSH
    # ----------------------------------------------------
    def on_commit_push(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        popup = tk.Toplevel(self)
        popup.title("Commit + Push")
        popup.geometry("400x200")

        ttk.Label(popup, text="Mensagem do commit:").pack(pady=10)
        msg_var = tk.StringVar()
        entry = ttk.Entry(popup, textvariable=msg_var, width=45)
        entry.pack(pady=5)

        def enviar():
            msg = msg_var.get().strip()
            if not msg:
                messagebox.showwarning("Aviso", "Informe uma mensagem de commit.")
                return
            try:
                branch = get_current_branch(self.repo_path)
                run_git_command(self.repo_path, ["add", "."])
                run_git_command(self.repo_path, ["commit", "-m", msg])
                run_git_command(self.repo_path, ["push", "-u", "origin", branch])
                messagebox.showinfo("Sucesso", f"✅ Commit enviado para 'origin/{branch}'.")
                self.log(f"Commit + push concluído em {branch}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao enviar commit: {e}")

        ttk.Button(popup, text="Commit e Enviar", command=enviar).pack(pady=10)

    # ----------------------------------------------------
    # RESOLVER CONFLITOS
    # ----------------------------------------------------
    def on_resolver_conflitos(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return
        try:
            run_git_command(self.repo_path, ["merge", "--continue"])
            messagebox.showinfo("Sucesso", "✅ Conflitos resolvidos com sucesso (merge continuado).")
            self.log("Conflitos resolvidos e merge finalizado.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao resolver conflitos: {e}")

    # ----------------------------------------------------
    # DELETAR TODAS AS BRANCHES LOCAIS (menos develop/main/master)
    # ----------------------------------------------------
    def on_deletar_todas(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        confirm = messagebox.askyesno("Confirmação",
                                      "Deseja realmente deletar TODAS as branches locais (exceto main, master e develop)?")
        if not confirm:
            return

        try:
            branches_output = run_git_command(self.repo_path, ["branch"]).splitlines()
            branches = [b.replace("*", "").strip() for b in branches_output if b.strip()]
            protegidas = ["main", "master", "develop"]
            deletadas = []

            for branch in branches:
                if branch not in protegidas:
                    try:
                        run_git_command(self.repo_path, ["branch", "-D", branch])
                        deletadas.append(branch)
                    except Exception:
                        pass

            if deletadas:
                messagebox.showinfo("Sucesso", f"🧹 Branches deletadas: {', '.join(deletadas)}")
                self.log(f"Branches removidas: {', '.join(deletadas)}")
            else:
                messagebox.showinfo("Aviso", "Nenhuma branch foi deletada (todas protegidas).")

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao deletar branches: {e}")

    # ----------------------------------------------------
    # DELETAR BRANCH LOCAL (escolher)
    # ----------------------------------------------------
    def on_deletar_local(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        branches_output = run_git_command(self.repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in branches_output if b.strip()]
        popup = tk.Toplevel(self)
        popup.title("Deletar Branch Local")
        popup.geometry("400x200")

        ttk.Label(popup, text="Selecione uma branch local para deletar:").pack(pady=10)
        var = tk.StringVar(value=branches[0])
        combo = ttk.Combobox(popup, textvariable=var, values=branches, state="readonly", width=40)
        combo.pack(pady=5)

        def deletar():
            branch = var.get()
            if branch in ["main", "master", "develop"]:
                messagebox.showwarning("Protegida", f"⚠️ Branch '{branch}' é protegida e não pode ser deletada.")
                return
            try:
                run_git_command(self.repo_path, ["branch", "-D", branch])
                messagebox.showinfo("Sucesso", f"🗑️ Branch local '{branch}' removida com sucesso.")
                self.log(f"Branch local deletada: {branch}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao deletar branch local: {e}")

        ttk.Button(popup, text="Deletar", command=deletar).pack(pady=10)

    # ----------------------------------------------------
    # DELETAR BRANCH REMOTA (escolher)
    # ----------------------------------------------------
    def on_deletar_remota(self):
        if not self.repo_path:
            messagebox.showwarning("Atenção", "Selecione o repositório primeiro.")
            return

        branches_output = run_git_command(self.repo_path, ["branch", "-r"]).splitlines()
        branches = [b.strip().replace("origin/", "") for b in branches_output if "origin/" in b]

        popup = tk.Toplevel(self)
        popup.title("Deletar Branch Remota")
        popup.geometry("400x200")

        ttk.Label(popup, text="Selecione uma branch remota para deletar:").pack(pady=10)
        var = tk.StringVar(value=branches[0])
        combo = ttk.Combobox(popup, textvariable=var, values=branches, state="readonly", width=40)
        combo.pack(pady=5)

        def deletar():
            branch = var.get()
            if branch in ["main", "master", "develop"]:
                messagebox.showwarning("Protegida", f"⚠️ Branch '{branch}' é protegida e não pode ser deletada.")
                return
            try:
                run_git_command(self.repo_path, ["push", "origin", "--delete", branch])
                messagebox.showinfo("Sucesso", f"🗑️ Branch remota '{branch}' deletada com sucesso.")
                self.log(f"Branch remota removida: {branch}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao deletar branch remota: {e}")

        ttk.Button(popup, text="Deletar", command=deletar).pack(pady=10)
