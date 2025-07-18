def construir_interface(janela, repo_var, selecionar_repositorio, acao_atualizar_branch_principal,
                        acao_criar_branch, acao_commit, acao_commit_push, log_output):
    import tkinter as tk
    tk.Label(janela, text="Repositório Git:").pack(pady=5)
    tk.Entry(janela, textvariable=repo_var, width=60, state="readonly").pack(padx=10)
    tk.Button(janela, text="Selecionar Repositório", command=selecionar_repositorio).pack(pady=10)

    tk.Button(janela, text="Atualizar Branch Principal", command=acao_atualizar_branch_principal, width=40).pack(pady=5)
    tk.Button(janela, text="Criar Branch (feature/)", command=acao_criar_branch, width=40).pack(pady=5)
    tk.Button(janela, text="Fazer Commit", command=acao_commit, width=40).pack(pady=5)
    tk.Button(janela, text="Commit + Push", command=acao_commit_push, width=40).pack(pady=5)
    tk.Button(janela, text="Sair", command=janela.quit, width=40).pack(pady=20)

    log_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)