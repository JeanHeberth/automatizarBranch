# ui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.git_operations import get_current_branch, run_git_command, commit_and_push
from core.pr_operations import create_pull_request, list_open_pull_requests, merge_pull_request
from core.env_utils import require_github_token


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automação Git com Tkinter")
        self.geometry("700x900")
        self.repo_path = None
        self.repo_var = tk.StringVar()
        self.log_text = tk.Text(self, height=10, width=80, state="disabled")
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="Repositório Git:").pack(pady=(10, 5))
        ttk.Entry(self, textvariable=self.repo_var, width=80, state="readonly").pack()

        ttk.Button(self, text="Selecionar Repositório", command=self.on_select_repo).pack(pady=5)

        buttons = [
            ("Atualizar Branch", self.on_atualizar_branch),
            ("Checkout de Branch", self.on_checkout_branch),
            ("Criar Branch", self.on_criar_branch),
            ("Fazer Commit", self.on_fazer_commit),
            ("Commit + Push", self.on_commit_push),
            ("Criar Pull Request", self.on_criar_pr),
            ("Merge Pull Request", self.on_merge_pr),
            ("Resolver Conflitos", self.on_resolver_conflitos),
            ("Deletar Branch", self.on_deletar_branch),
            ("Deletar Branch Local", self.on_deletar_branch_local),
            ("Deletar Branch Remota", self.on_deletar_branch_remota),
            ("Sair", self.quit),
        ]

        for text, cmd in buttons:
            ttk.Button(self, text=text, command=cmd, width=40).pack(pady=5)

        ttk.Label(self, text="Logs de Execução:").pack(pady=(20, 5))
        self.log_text.pack(pady=5)

    # ================== LOGGING ======================
    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[LOG] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ================== REPOSITÓRIO ======================
    def on_select_repo(self):
        path = filedialog.askdirectory(title="Selecione o repositório Git")
        if path:
            self.repo_path = path
            self.repo_var.set(f"Repositório selecionado: {path}")
            self.log(f"Repositório: {path}")

    # ================== BRANCHES ======================
    def on_atualizar_branch(self):
        run_git_command(self.repo_path, ["pull"])
        self.log("Branch atualizada com sucesso.")

    def on_checkout_branch(self):
        output = run_git_command(self.repo_path, ["branch"])
        branches = [b.strip().replace("* ", "") for b in output.splitlines()]
        self._popup_selector("Checkout de Branch", "Escolha uma branch:", branches, self._checkout)

    def _checkout(self, branch):
        run_git_command(self.repo_path, ["checkout", branch])
        self.log(f"Checkout para branch {branch} realizado.")

    def on_criar_branch(self):
        name = self._popup_text("Criar Branch", "Nome da nova branch:")
        if name:
            run_git_command(self.repo_path, ["checkout", "-b", name])
            self.log(f"Branch {name} criada.")

    def on_fazer_commit(self):
        msg = self._popup_text("Commit", "Mensagem do commit:")
        if msg:
            run_git_command(self.repo_path, ["add", "."])
            run_git_command(self.repo_path, ["commit", "-m", msg])
            self.log(f"Commit realizado: {msg}")

    def on_commit_push(self):
        msg = self._popup_text("Commit + Push", "Mensagem do commit:")
        if msg:
            branch, remote = commit_and_push(self.repo_path, msg)
            self.log(f"Commit enviado para {remote}/{branch}.")

    # ================== PULL REQUEST ======================
    def on_criar_pr(self):
        branches = run_git_command(self.repo_path, ["branch"]).splitlines()
        branches = [b.replace("*", "").strip() for b in branches]
        popup = tk.Toplevel(self)
        popup.title("Criar Pull Request")
        popup.geometry("480x400")
        popup.resizable(False, False)

        ttk.Label(popup, text="Branch Base (para onde vai o PR):").pack(pady=5)
        base = tk.StringVar(value="main" if "main" in branches else branches[0])
        ttk.Combobox(popup, textvariable=base, values=branches, state="readonly", width=50).pack()

        ttk.Label(popup, text="Título do PR:").pack(pady=10)
        title_var = tk.StringVar(value=f"Merge {get_current_branch(self.repo_path)} → {base.get()}")
        ttk.Entry(popup, textvariable=title_var, width=50).pack()

        def confirmar():
            try:
                url = create_pull_request(self.repo_path, base=base.get(), title=title_var.get())
                messagebox.showinfo("Pull Request", f"PR criado com sucesso!\n{url}")
                self.log(f"PR criado: {url}")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                self.log(f"Erro ao criar PR: {e}")

        ttk.Button(popup, text="Criar Pull Request", command=confirmar).pack(pady=20)

    def on_merge_pr(self):
        """Abre popup para listar e mesclar PRs abertos."""
        try:
            prs = list_open_pull_requests(self.repo_path)
            if not prs:
                messagebox.showinfo("Merge Pull Request", "Nenhum PR aberto encontrado.")
                return

            popup = tk.Toplevel(self)
            popup.title("Merge Pull Request")
            popup.geometry("480x300")
            popup.resizable(False, False)

            ttk.Label(popup, text="Selecione o PR para merge:").pack(pady=10)
            pr_var = tk.StringVar(value=prs[0])
            ttk.Combobox(popup, textvariable=pr_var, values=prs, state="readonly", width=60).pack(pady=10)

            def confirmar_merge():
                pr_number = pr_var.get().split("—")[0].replace("#", "").strip()
                try:
                    result = merge_pull_request(self.repo_path, pr_number)
                    messagebox.showinfo("Merge Pull Request", f"✅ Merge concluído com sucesso!\nPR #{pr_number}")
                    self.log(f"Merge concluído: {result}")
                    popup.destroy()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))
                    self.log(f"Erro ao fazer merge: {e}")

            ttk.Button(popup, text="Fazer Merge", command=confirmar_merge).pack(pady=20)

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao abrir lista de PRs: {e}")

    def on_resolver_conflitos(self):
        messagebox.showinfo("Resolver Conflitos", "Função em desenvolvimento.")

    # ================== DELEÇÃO ======================
    def on_deletar_branch(self):
        output = run_git_command(self.repo_path, ["branch"])
        branches = [b.strip().replace("* ", "") for b in output.splitlines()]
        protected = ["main", "master", "develop", get_current_branch(self.repo_path)]
        deletables = [b for b in branches if b not in protected]
        if not deletables:
            messagebox.showinfo("Nenhuma branch", "Nenhuma branch disponível para deleção.")
            return
        for b in deletables:
            run_git_command(self.repo_path, ["branch", "-D", b])
        self.log(f"Branches deletadas: {', '.join(deletables)}")

    def on_deletar_branch_local(self):
        output = run_git_command(self.repo_path, ["branch"])
        branches = [b.strip().replace("* ", "") for b in output.splitlines()]
        self._popup_selector("Deletar Branch Local", "Escolha uma branch:", branches, self._delete_branch)

    def _delete_branch(self, branch):
        run_git_command(self.repo_path, ["branch", "-D", branch])
        self.log(f"Branch local {branch} deletada.")

    def on_deletar_branch_remota(self):
        output = run_git_command(self.repo_path, ["branch", "-r"])
        branches = [b.replace("origin/", "").strip() for b in output.splitlines()]
        self._popup_selector("Deletar Branch Remota", "Escolha uma branch:", branches, self._delete_remote_branch)

    def _delete_remote_branch(self, branch):
        run_git_command(self.repo_path, ["push", "origin", "--delete", branch])
        self.log(f"Branch remota {branch} deletada.")

    # ================== POPUPS ======================
    def _popup_selector(self, title, label, options, callback):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("400x200")
        ttk.Label(popup, text=label).pack(pady=10)
        var = tk.StringVar(value=options[0])
        combo = ttk.Combobox(popup, textvariable=var, values=options, state="readonly")
        combo.pack(pady=10)
        ttk.Button(popup, text="Confirmar", command=lambda: (callback(var.get()), popup.destroy())).pack(pady=10)
        popup.wait_window()

    def _popup_text(self, title, label):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("400x200")
        ttk.Label(popup, text=label).pack(pady=10)
        var = tk.StringVar()
        ttk.Entry(popup, textvariable=var, width=50).pack(pady=10)
        ttk.Button(popup, text="Confirmar", command=popup.destroy).pack(pady=10)
        popup.wait_window()
        return var.get()


