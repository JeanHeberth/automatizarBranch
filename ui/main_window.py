# ui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

from core.git_operations import (
    create_branch,
    commit_and_push,
    get_current_branch,
    run_git_command,
    GitCommandError,
)
from core.pr_operations import create_pull_request, merge_pull_request
from utils.repo_utils import try_get_repo_info


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automacao Git com Tkinter")
        self.configure(bg="#F0F0F0")
        self.resizable(False, False)
        self.geometry("760x880")

        self.repo_path: Path | None = None
        self._build_ui()

    # --------------------------------------------------
    # Interface
    # --------------------------------------------------
    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=40, pady=25)

        ttk.Label(container, text="Repositório Git:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.entry_repo = ttk.Entry(container, width=70)
        self.entry_repo.state(["disabled"])
        self.entry_repo.grid(row=1, column=0, sticky="ew")

        ttk.Button(container, text="Selecionar Repositório", command=self.select_repo).grid(
            row=2, column=0, pady=(12, 18)
        )

        buttons_frame = ttk.Frame(container)
        buttons_frame.grid(row=3, column=0, sticky="ew")

        BTN_WIDTH = 38
        BTN_PADY = 8

        # Botões de ações Git
        self._add_button(buttons_frame, "Atualizar Branch", self.on_atualizar_branch, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Checkout de Branch", self.on_checkout_branch, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Criar Branch", self.on_criar_branch, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Fazer Commit", self.on_fazer_commit, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Commit + Push", self.on_commit_push, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Criar Pull Request", self.on_criar_pr, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Merge Pull Request", self.on_merge_pr, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Resolver Conflitos", self.on_resolver_conflitos, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Deletar Branch", self.on_deletar_branch, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Deletar Branch Local", self.on_deletar_branch_local, BTN_WIDTH, BTN_PADY)
        self._add_button(buttons_frame, "Deletar Branch Remota", self.on_deletar_branch_remota, BTN_WIDTH, BTN_PADY)
        ttk.Button(buttons_frame, text="Sair", command=self.quit, width=BTN_WIDTH).pack(pady=(BTN_PADY, 0))

        # Console de logs
        ttk.Label(container, text="Logs de Execução:").grid(row=4, column=0, sticky="w", pady=(20, 5))
        self.log_text = tk.Text(container, height=8, width=80, state="disabled", background="#f7f7f7")
        self.log_text.grid(row=5, column=0, sticky="ew")

    def _add_button(self, parent, text, command, width, pady):
        ttk.Button(parent, text=text, command=command, width=width).pack(pady=pady)

    # --------------------------------------------------
    # Logs
    # --------------------------------------------------
    def log(self, message: str):
        """Adiciona mensagem ao console interno."""
        self.log_text.config(state="normal")
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_text.insert("end", f"{timestamp} {message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    # --------------------------------------------------
    # Atualização do label
    # --------------------------------------------------
    def update_repo_label(self):
        """Atualiza o texto do campo de repositório com a branch atual."""
        if not self.repo_path:
            return
        info = try_get_repo_info(self.repo_path)
        if not info:
            return
        current_branch = get_current_branch(self.repo_path)
        summary = f"{info.full_name} ({info.host}) — Branch atual: {current_branch}"

        self.entry_repo.state(["!disabled"])
        self.entry_repo.delete(0, tk.END)
        self.entry_repo.insert(0, summary)
        self.entry_repo.state(["disabled"])

    # --------------------------------------------------
    # Funções principais
    # --------------------------------------------------
    def select_repo(self):
        path = filedialog.askdirectory(title="Selecione a pasta do repositório Git")
        if not path:
            return
        self.repo_path = Path(path)
        self.log(f"Repositório selecionado: {self.repo_path}")
        self.update_repo_label()

    def on_atualizar_branch(self):
        branch = self._popup_branch_selector("Atualizar Branch", "Selecione uma branch:", self._get_branches())
        if not branch:
            return
        try:
            self.log(f"Atualizando branch '{branch}'...")
            run_git_command(self.repo_path, ["checkout", branch])
            run_git_command(self.repo_path, ["pull"])
            self.update_repo_label()
            messagebox.showinfo("Atualização", f"Branch '{branch}' atualizada com sucesso!")
            self.log(f"Branch '{branch}' atualizada com sucesso.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao atualizar branch: {e}")

    def on_checkout_branch(self):
        branch = self._popup_branch_selector("Checkout de Branch", "Selecione uma branch:", self._get_branches())
        if not branch:
            return
        try:
            self.log(f"Realizando checkout para '{branch}'...")
            run_git_command(self.repo_path, ["checkout", branch])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Feito checkout para: {branch}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao realizar checkout: {e}")

    def on_criar_branch(self):
        branch = self._popup_text_input("Criar Branch", "Nome da nova branch:")
        if not branch:
            return
        try:
            self.log(f"Criando nova branch '{branch}'...")
            create_branch(self.repo_path, branch)
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Branch '{branch}' criada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao criar branch: {e}")

    def on_fazer_commit(self):
        msg = self._popup_text_input("Fazer Commit", "Mensagem do commit:")
        if not msg:
            return
        try:
            self.log(f"Criando commit: {msg}")
            run_git_command(self.repo_path, ["add", "."])
            run_git_command(self.repo_path, ["commit", "-m", msg])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Commit criado:\n\n{msg}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao realizar commit: {e}")

    def on_commit_push(self):
        msg = self._popup_text_input("Commit + Push", "Mensagem do commit:")
        if not msg:
            return
        try:
            self.log(f"Realizando commit e push: {msg}")
            branch, remote = commit_and_push(self.repo_path, msg)
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Commit enviado!\n\nBranch: {branch}\nRepo: {remote}")
            self.log(f"Commit + push enviados para '{remote}/{branch}'.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao enviar push: {e}")

    def on_criar_pr(self):
        branches = [b for b in self._get_branches() if b != "main"]
        branch = self._popup_branch_selector("Criar Pull Request", "Selecione a branch para o PR:", branches)
        if not branch:
            return
        try:
            self.log(f"Criando Pull Request para '{branch}'...")
            pr_url = create_pull_request(self.repo_path, base="main", title=f"Merge {branch}", body="")
            messagebox.showinfo("Pull Request", f"Pull Request criado!\n\n{pr_url}")
            self.log(f"PR criado com sucesso: {pr_url}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao criar PR: {e}")

    def on_merge_pr(self):
        prs = self._get_pull_requests()
        pr = self._popup_branch_selector("Merge Pull Request", "Selecione o PR para merge:", prs)
        if not pr:
            return
        try:
            self.log(f"Fazendo merge do {pr}...")
            merge_pull_request(self.repo_path, pr.split("#")[-1])
            self.update_repo_label()
            messagebox.showinfo("Merge", f"Pull Request {pr} mergeado com sucesso!")
            self.log(f"Merge realizado com sucesso para {pr}.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao fazer merge: {e}")

    def on_resolver_conflitos(self):
        branches = self._get_branches()
        branch = self._popup_branch_selector("Resolver Conflitos", "Selecione a branch em conflito:", branches)
        if not branch:
            return
        try:
            self.log(f"Resolvendo conflitos em '{branch}'...")
            run_git_command(self.repo_path, ["merge", branch])
            self.update_repo_label()
            messagebox.showinfo("Conflitos", f"Conflitos resolvidos na branch '{branch}'.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao resolver conflitos: {e}")

    # --------------------------------------------------
    # 🔥 Deleção de branches (3 modos)
    # --------------------------------------------------
    def on_deletar_branch(self):
        """Deleta todas as branches locais, exceto a develop e a atual."""
        try:
            branches = self._get_branches()
            current = get_current_branch(self.repo_path)
            safe_branches = ["develop", current]
            deletables = [b for b in branches if b not in safe_branches]

            if not deletables:
                messagebox.showinfo("Deletar Branches", "Nenhuma branch local disponível para deleção.")
                return

            confirm = messagebox.askyesno(
                "Confirmação",
                f"Você tem certeza que deseja deletar {len(deletables)} branches locais?\n\n"
                + "\n".join(f"- {b}" for b in deletables)
            )
            if not confirm:
                return

            deleted = []
            ignored = []

            for branch in deletables:
                try:
                    run_git_command(self.repo_path, ["branch", "-D", branch])
                    deleted.append(branch)
                    self.log(f"Branch '{branch}' deletada.")
                except GitCommandError as e:
                    ignored.append(branch)
                    self.log(f"Não foi possível deletar '{branch}': {e}")

            self.update_repo_label()

            resumo = f"✅ Deletadas: {', '.join(deleted) if deleted else 'nenhuma'}"
            if ignored:
                resumo += f"\n⚠️ Ignoradas (em uso): {', '.join(ignored)}"

            messagebox.showinfo("Resultado da Limpeza", resumo)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao deletar branches: {e}")

    def on_deletar_branch_local(self):
        """Permite escolher uma branch local para deletar."""
        branches = self._get_branches()
        current = get_current_branch(self.repo_path)
        choices = [b for b in branches if b != current and b != "develop"]
        branch = self._popup_branch_selector("Deletar Branch Local", "Selecione uma branch local para deletar:",
                                             choices)
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["branch", "-D", branch])
            self.update_repo_label()
            self.log(f"Branch local '{branch}' deletada.")
            messagebox.showinfo("Sucesso", f"Branch local '{branch}' deletada.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao deletar branch local: {e}")

    def on_deletar_branch_remota(self):
        """Permite escolher uma branch remota e deletar via push --delete."""
        branches = self._get_remote_branches()
        choices = [b for b in branches if b != "develop"]
        branch = self._popup_branch_selector("Deletar Branch Remota", "Selecione uma branch remota para deletar:",
                                             choices)
        if not branch:
            return
        confirm = messagebox.askyesno("Confirmação", f"Deseja realmente deletar a branch remota '{branch}'?")
        if not confirm:
            return
        try:
            run_git_command(self.repo_path, ["push", "origin", "--delete", branch])
            self.update_repo_label()
            self.log(f"Branch remota '{branch}' deletada.")
            messagebox.showinfo("Sucesso", f"Branch remota '{branch}' deletada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro ao deletar branch remota: {e}")

    # --------------------------------------------------
    # Métodos utilitários e popups
    # --------------------------------------------------
    def _get_branches(self):
        if not self.repo_path:
            return []
        branches = run_git_command(self.repo_path, ["branch"]).splitlines()
        return [b.strip().replace("* ", "") for b in branches if b.strip()]

    def _get_remote_branches(self):
        if not self.repo_path:
            return []
        branches = run_git_command(self.repo_path, ["branch", "-r"]).splitlines()
        return [b.strip().replace("origin/", "") for b in branches if "origin/" in b]

    def _get_pull_requests(self):
        """Busca PRs abertos via GitHub API."""
        try:
            from core.pr_operations import list_open_pull_requests
            prs = list_open_pull_requests(self.repo_path)
            return prs or ["Nenhum Pull Request aberto."]
        except Exception as e:
            messagebox.showerror("Erro ao buscar PRs", str(e))
            self.log(f"Erro ao buscar PRs: {e}")
            return []

    def _popup_text_input(self, title, prompt):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("400x150")
        popup.resizable(False, False)
        ttk.Label(popup, text=prompt).pack(pady=10)
        entry = ttk.Entry(popup, width=45)
        entry.pack(pady=5)
        result = {"value": None}

        def confirm():
            result["value"] = entry.get().strip()
            popup.destroy()

        ttk.Button(popup, text="Confirmar", command=confirm).pack(pady=10)
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)
        return result["value"]

    def _popup_branch_selector(self, title, prompt, options):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("400x180")
        popup.resizable(False, False)

        ttk.Label(popup, text=prompt).pack(pady=10)
        selected = tk.StringVar()
        combo = ttk.Combobox(popup, textvariable=selected, values=options, state="readonly", width=42)
        if options:
            combo.current(0)
        combo.pack(pady=5)
        result = {"value": None}

        def confirm():
            result["value"] = selected.get().strip()
            popup.destroy()

        ttk.Button(popup, text="Confirmar", command=confirm).pack(pady=10)
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)
        return result["value"]
