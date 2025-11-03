# ui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from core.git_operations import (
    create_branch,
    commit_and_push,
    merge_to_main,
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
        self.geometry("760x820")

        self.repo_path: Path | None = None
        self._build_ui()

    # --------------------------------------------------
    # UI
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

        # Ordem idêntica ao layout
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

    def _add_button(self, parent, text, command, width, pady):
        ttk.Button(parent, text=text, command=command, width=width).pack(pady=pady)

    # --------------------------------------------------
    # Atualiza label do repositório
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
    # Funções Git
    # --------------------------------------------------
    def select_repo(self):
        path = filedialog.askdirectory(title="Selecione a pasta do repositório Git")
        if not path:
            return
        self.repo_path = Path(path)
        self.update_repo_label()

    def on_atualizar_branch(self):
        branch = self._popup_branch_selector("Atualizar Branch", "Selecione uma branch:", self._get_branches())
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["checkout", branch])
            run_git_command(self.repo_path, ["pull"])
            self.update_repo_label()
            messagebox.showinfo("Atualização", f"Branch '{branch}' atualizada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_checkout_branch(self):
        branch = self._popup_branch_selector("Checkout de Branch", "Selecione uma branch:", self._get_branches())
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["checkout", branch])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Feito checkout para: {branch}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_criar_branch(self):
        branch = self._popup_text_input("Criar Branch", "Nome da nova branch:")
        if not branch:
            return
        try:
            create_branch(self.repo_path, branch)
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Branch '{branch}' criada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_fazer_commit(self):
        msg = self._popup_text_input("Fazer Commit", "Mensagem do commit:")
        if not msg:
            return
        try:
            run_git_command(self.repo_path, ["add", "."])
            run_git_command(self.repo_path, ["commit", "-m", msg])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Commit criado:\n\n{msg}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_commit_push(self):
        msg = self._popup_text_input("Commit + Push", "Mensagem do commit:")
        if not msg:
            return
        try:
            branch, remote = commit_and_push(self.repo_path, msg)
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Commit enviado!\n\nBranch: {branch}\nRepo: {remote}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_criar_pr(self):
        branches = [b for b in self._get_branches() if b != "main"]
        branch = self._popup_branch_selector("Criar Pull Request", "Selecione a branch para o PR:", branches)
        if not branch:
            return
        try:
            pr_url = create_pull_request(self.repo_path, base="main", title=f"Merge {branch}", body="")
            messagebox.showinfo("Pull Request", f"Pull Request criado!\n\n{pr_url}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_merge_pr(self):
        prs = self._get_pull_requests()
        pr = self._popup_branch_selector("Merge Pull Request", "Selecione o PR para merge:", prs)
        if not pr:
            return
        try:
            merge_pull_request(self.repo_path, pr.split("#")[-1])
            self.update_repo_label()
            messagebox.showinfo("Merge", f"Pull Request {pr} mergeado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_resolver_conflitos(self):
        branches = self._get_branches()
        branch = self._popup_branch_selector("Resolver Conflitos", "Selecione a branch em conflito:", branches)
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["merge", branch])
            self.update_repo_label()
            messagebox.showinfo("Conflitos", f"Conflitos resolvidos na branch '{branch}'.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_deletar_branch(self):
        branch = self._popup_branch_selector("Deletar Branch", "Selecione a branch:", self._get_branches())
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["branch", "-D", branch])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Branch '{branch}' deletada.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_deletar_branch_local(self):
        self.on_deletar_branch()

    def on_deletar_branch_remota(self):
        branches = self._get_remote_branches()
        branch = self._popup_branch_selector("Deletar Branch Remota", "Selecione a branch remota:", branches)
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["push", "origin", "--delete", branch])
            self.update_repo_label()
            messagebox.showinfo("Sucesso", f"Branch remota '{branch}' deletada.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

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
        # Exemplo fictício até integrar listagem real via API
        return ["#1 Ajuste no login", "#2 Nova feature relatórios", "#3 Hotfix deploy"]

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
