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

        # Ordem idêntica ao exemplo
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

        container.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(0, weight=1)

    def _add_button(self, parent, text, command, width, pady):
        ttk.Button(parent, text=text, command=command, width=width).pack(pady=pady)

    # --------------------------------------------------
    # Ações Git
    # --------------------------------------------------
    def select_repo(self):
        path = filedialog.askdirectory(title="Selecione a pasta do repositório Git")
        if not path:
            return
        self.repo_path = Path(path)
        info = try_get_repo_info(self.repo_path)
        self.entry_repo.state(["!disabled"])
        self.entry_repo.delete(0, tk.END)
        if info:
            summary = f"{info.full_name} ({info.host}) — Branch atual: {get_current_branch(self.repo_path)}"
            self.entry_repo.insert(0, summary)
        else:
            self.entry_repo.insert(0, "⚠️ Repositório inválido ou sem remoto configurado.")
        self.entry_repo.state(["disabled"])

    def on_atualizar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        try:
            run_git_command(self.repo_path, ["pull"])
            messagebox.showinfo("Atualização", "Branch atualizada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_checkout_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        branch = self._input_popup("Checkout de Branch", "Informe o nome da branch:")
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["checkout", branch])
            messagebox.showinfo("Sucesso", f"Feito checkout para: {branch}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_criar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        branch = self._input_popup("Criar Branch", "Nome da nova branch:")
        if not branch:
            return
        try:
            create_branch(self.repo_path, branch)
            messagebox.showinfo("Sucesso", f"Branch '{branch}' criada com sucesso!")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_fazer_commit(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        msg = self._input_popup("Fazer Commit", "Mensagem do commit:")
        if not msg:
            return
        try:
            run_git_command(self.repo_path, ["add", "."])
            run_git_command(self.repo_path, ["commit", "-m", msg])
            messagebox.showinfo("Sucesso", f"Commit criado:\n\n{msg}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_commit_push(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        msg = self._input_popup("Commit + Push", "Mensagem do commit:")
        if not msg:
            return
        try:
            branch, remote = commit_and_push(self.repo_path, msg)
            messagebox.showinfo("Sucesso", f"Commit enviado!\n\nBranch: {branch}\nRepo: {remote}")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_criar_pr(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        title = self._input_popup("Criar Pull Request", "Título do Pull Request:")
        if not title:
            return
        try:
            pr_url = create_pull_request(self.repo_path, title=title)
            messagebox.showinfo("Pull Request", f"Pull Request criado com sucesso!\n\n{pr_url}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_merge_pr(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        pr_number = self._input_popup("Merge Pull Request", "Número do Pull Request:")
        if not pr_number:
            return
        try:
            merge_pull_request(self.repo_path, pr_number)
            messagebox.showinfo("Merge", f"Pull Request #{pr_number} mergeado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_resolver_conflitos(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        try:
            run_git_command(self.repo_path, ["merge", "--continue"])
            messagebox.showinfo("Conflitos", "Processo de merge continuado após resolução.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_deletar_branch(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        branch = self._input_popup("Deletar Branch", "Nome da branch:")
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["branch", "-D", branch])
            messagebox.showinfo("Sucesso", f"Branch '{branch}' deletada localmente.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    def on_deletar_branch_local(self):
        self.on_deletar_branch()

    def on_deletar_branch_remota(self):
        if not self.repo_path:
            return messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
        branch = self._input_popup("Deletar Branch Remota", "Nome da branch remota:")
        if not branch:
            return
        try:
            run_git_command(self.repo_path, ["push", "origin", "--delete", branch])
            messagebox.showinfo("Sucesso", f"Branch remota '{branch}' deletada.")
        except GitCommandError as e:
            messagebox.showerror("Erro", str(e))

    # --------------------------------------------------
    # Utilitários
    # --------------------------------------------------
    def _input_popup(self, title, prompt):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("350x150")
        popup.resizable(False, False)
        ttk.Label(popup, text=prompt).pack(pady=10)
        entry = ttk.Entry(popup, width=40)
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
