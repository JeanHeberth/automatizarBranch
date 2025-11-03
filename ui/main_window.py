# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from core.git_operations import (
    get_repo_info_summary,
    get_current_branch,
    create_branch,
    commit_and_push,
    merge_to_main,
    GitCommandError,
)
from utils.repo_utils import try_get_repo_info

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Automação de Branches")
        self.geometry("620x480")
        self.resizable(False, False)
        self.configure(bg="#111")

        self.repo_path: Path | None = None

        self._build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        # Cabeçalho
        header = tk.Frame(self, bg="#111")
        header.pack(pady=(20, 10))

        tk.Label(
            header,
            text="Automação de Branches 🧠",
            font=("Segoe UI", 18, "bold"),
            bg="#111",
            fg="#00d4ff",
        ).pack()

        tk.Label(
            header,
            text="Gerencie branches, commits e merges de forma rápida e visual.",
            font=("Segoe UI", 10),
            bg="#111",
            fg="#bbb",
        ).pack()

        # Linha divisória
        tk.Frame(self, bg="#222", height=2, width=580).pack(pady=10)

        # Seção de repositório
        repo_frame = tk.Frame(self, bg="#111")
        repo_frame.pack(pady=10)

        tk.Button(
            repo_frame,
            text="📁 Selecionar Repositório",
            font=("Segoe UI", 11, "bold"),
            bg="#00d4ff",
            fg="black",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            activebackground="#00aee0",
            command=self.select_repo,
        ).pack()

        self.lbl_repo_info = tk.Label(
            self,
            text="Nenhum repositório selecionado",
            font=("Segoe UI", 10),
            bg="#111",
            fg="#fff",
        )
        self.lbl_repo_info.pack(pady=(8, 0))

        self.lbl_branch = tk.Label(
            self,
            text="",
            font=("Segoe UI", 10),
            bg="#111",
            fg="#9efbff",
        )
        self.lbl_branch.pack()

        # Campos
        self._styled_entry("🌿 Nova branch (feature/...):", "branch")
        self._styled_entry("💬 Mensagem de commit:", "commit")

        # Botões de ação
        btns = tk.Frame(self, bg="#111")
        btns.pack(pady=25)

        self._add_action_button(btns, "🪴 Criar Branch", self.handle_create_branch, 0)
        self._add_action_button(btns, "💾 Commit & Push", self.handle_commit_push, 1)
        self._add_action_button(btns, "🔀 Merge → main", self.handle_merge_main, 2)

        # Rodapé / status
        self.lbl_status = tk.Label(
            self,
            text="Pronto.",
            font=("Segoe UI", 9),
            bg="#111",
            fg="#888",
        )
        self.lbl_status.pack(side="bottom", pady=10)

    def _styled_entry(self, label_text: str, key: str):
        """Cria label e campo de entrada com estilo moderno."""
        frame = tk.Frame(self, bg="#111")
        frame.pack(pady=8)

        tk.Label(frame, text=label_text, bg="#111", fg="#fff", font=("Segoe UI", 10)).pack(anchor="w")

        entry = tk.Entry(
            frame,
            width=45,
            bg="#222",
            fg="#fff",
            insertbackground="#00d4ff",
            relief="flat",
            font=("Segoe UI", 10),
        )
        entry.pack(ipady=5, pady=(2, 0))

        setattr(self, f"entry_{key}", entry)

    def _add_action_button(self, parent, text, command, row):
        """Cria botões com estilo moderno e hover."""
        def on_enter(e):
            btn.config(bg="#00aee0")

        def on_leave(e):
            btn.config(bg="#00d4ff")

        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg="#00d4ff",
            fg="black",
            relief="flat",
            width=25,
            height=2,
            command=command,
        )
        btn.grid(row=row, column=0, pady=5)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # --------------------------------------------------
    # Ações
    # --------------------------------------------------
    def select_repo(self):
        path = filedialog.askdirectory(title="Selecione a pasta do repositório Git")
        if not path:
            return

        self.repo_path = Path(path)
        info = try_get_repo_info(self.repo_path)
        if info:
            summary = f"{info.full_name} ({info.host})"
            branch = get_current_branch(self.repo_path)
            self.lbl_repo_info.config(text=f"📂 {summary}")
            self.lbl_branch.config(text=f"🌿 Branch atual: {branch}")
            self._set_status(f"Repositório carregado: {summary}")
        else:
            self.lbl_repo_info.config(text="⚠️ Repositório inválido ou sem remoto configurado.")
            self.lbl_branch.config(text="")
            self._set_status("Erro ao ler o repositório.")

    def handle_create_branch(self):
        if not self.repo_path:
            messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
            return

        name = self.entry_branch.get().strip()
        if not name:
            messagebox.showinfo("Info", "Informe o nome da nova branch (ex: feature/minha-funcionalidade).")
            return

        try:
            created = create_branch(self.repo_path, name)
            self.lbl_branch.config(text=f"🌿 Nova branch: {created}")
            self._set_status(f"Branch criada: {created}")
            messagebox.showinfo("Sucesso", f"Branch '{created}' criada com sucesso!")
        except GitCommandError as e:
            self._set_status("Erro ao criar branch.")
            messagebox.showerror("Erro ao criar branch", str(e))

    def handle_commit_push(self):
        if not self.repo_path:
            messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
            return

        msg = self.entry_commit.get().strip()
        if not msg:
            messagebox.showinfo("Info", "Informe uma mensagem de commit.")
            return

        try:
            branch, remote = commit_and_push(self.repo_path, msg)
            self._set_status(f"Commit enviado ({branch})")
            messagebox.showinfo("Sucesso", f"✅ Commit enviado!\n\nBranch: {branch}\nRepo: {remote}")
        except GitCommandError as e:
            self._set_status("Erro ao enviar commit.")
            messagebox.showerror("Erro ao enviar commit", str(e))

    def handle_merge_main(self):
        if not self.repo_path:
            messagebox.showwarning("Aviso", "Selecione um repositório primeiro.")
            return

        try:
            merge_to_main(self.repo_path)
            self._set_status("Merge concluído.")
            messagebox.showinfo("Merge", "Merge concluído com sucesso!")
        except GitCommandError as e:
            self._set_status("Erro ao fazer merge.")
            messagebox.showerror("Erro ao fazer merge", str(e))

    def _set_status(self, text: str):
        """Atualiza o status na barra inferior."""
        self.lbl_status.config(text=text)
