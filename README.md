# 🧠 Automação Git com Tkinter

Aplicativo com interface gráfica em Tkinter para facilitar ações Git como:

- Seleção de repositório
- Criação de branches (feature/)
- Commit e push
- Atualização da branch principal (`main` ou `master`)
- **Checkout de branches existentes**
- **Exclusão (delete) de branches locais**
- **Criação e merge de Pull Requests (PR)**
- Visualização de logs dos comandos executados

---

## ✅ Funcionalidades

- ✨ Interface simples e intuitiva em Tkinter
- 🚀 Operações Git automatizadas sem congelamento de UI
- 📊 Dropdowns interativos para seleção de branches
- 📝 Logging estruturado com arquivo rotativo
- 🔐 Segurança integrada (validação de repositório, token em .env)
- ⚡ Cache inteligente para reduzir chamadas Git
- 🧪 Suite de testes automatizados com pytest
- 🔄 CI/CD com GitHub Actions
- 📱 Threading para operações assíncronas

---

## 🛠️ Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/JeanHeberth/automatizarBranch.git
   cd automatizarBranch
   ```

2. Crie o ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Linux/macOS
   .venv\Scripts\activate         # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure autenticação GitHub (escolha uma):
   ```bash
   # ⭐ RECOMENDADO: GitHub CLI
   brew install gh
   gh auth login
   
   # OU: Git Credential Manager (integrado com Windows/macOS)
   # OU: Token em .env (apenas desenvolvimento local, inseguro)
   ```

> 🔐 Veja `SECURE_AUTH.md` para guia completo de autenticação segura!

---

## 🚀 Execução

### Modo Normal
```bash
python main.py
```

### Modo com Debug
```bash
DEBUG=1 python main.py
```

---

## 🖥️ Como usar

1. Clique em **Selecionar Repositório** e escolha a pasta do seu projeto Git.
   - ✅ A pasta deve conter `.git/` para ser válida
2. Use os botões da interface para:
    - Criar uma nova branch `feature/<nome>`
    - Fazer commit e/ou push das alterações
    - Atualizar a branch principal (main/master)
    - **Trocar de branch (checkout)** via dropdown
    - **Deletar branch local** com segurança
    - **Criar Pull Request automaticamente**
    - **Merge de PR** (automático ou manual com número)
3. Os logs aparecem em tempo real na interface
4. Logs também são salvos em `logs/git_automation.log`

---

## 🧪 Testes

### Rodar todos os testes
```bash
pytest
```

### Rodar testes com cobertura
```bash
pytest --cov=. --cov-report=html
```

### Rodar testes específicos
```bash
pytest tests/test_git_operations.py -v
pytest tests/test_branch_service.py::TestBranchService::test_list_branches -v
```

### Marcadores de teste
```bash
pytest -m unit      # Apenas testes unitários
pytest -m git       # Testes que requerem Git
```

---

## 📂 Estrutura do Projeto

```
automatizarBranch/
├── main.py                          # Ponto de entrada
├── requirements.txt                 # Dependências
├── pytest.ini                       # Configuração de testes
├── .gitignore                       # Arquivos ignorados
├── .env                             # Variáveis de ambiente (⚠️ NÃO commitar)
│
├── core/
│   ├── git_operations.py            # Operações base de Git
│   ├── pr_operations.py             # Operações de PR (movido para services/)
│   ├── env_utils.py                 # Utilidades de variáveis de ambiente
│   ├── logger_config.py             # ✨ Novo: Sistema de logging
│   └── cache.py                     # ✨ Novo: Sistema de cache com TTL
│
├── services/
│   ├── branch_service.py            # Operações de branches
│   ├── commit_service.py            # Operações de commit
│   ├── pr_service.py                # Serviços de PR
│   ├── delete_service.py            # Deleção de branches
│   ├── rollback_service.py          # Rollback de commits
│   └── pr_operations.py             # ✨ Novo: Movido de core/
│
├── ui/
│   └── main_window.py               # Interface Tkinter
│
├── utils/
│   ├── repo_utils.py                # Utilidades de repositório
│   └── worker_thread.py             # ✨ Novo: Threading para UI assíncrona
│
├── tests/                           # ✨ Novo: Testes automatizados
│   ├── conftest.py                  # Fixtures compartilhadas
│   ├── test_git_operations.py       # Testes de git_operations
│   └── test_branch_service.py       # Testes de branch_service
│
├── logs/                            # ✨ Novo: Diretório de logs (gerado automaticamente)
│   └── git_automation.log           # Log rotativo
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml                # ✨ Novo: CI/CD GitHub Actions
│
└── README.md
```

---

## 🔐 Segurança

### Token do GitHub
- O token é armazenado em `.env` (não versionado)
- Use um **Personal Access Token (PAT)** com permissões limitadas
- Para criar: Settings → Developer settings → Personal access tokens

### .gitignore
O projeto protege automaticamente:
- `*.log` - Logs do sistema
- `.env` - Variáveis de ambiente
- `__pycache__/` - Arquivos Python compilados
- `.venv/` - Ambiente virtual

---

## 📊 Logging

### Arquivos de Log
- **Local**: `logs/git_automation.log`
- **Rotação**: Máx 1MB por arquivo, até 5 backups
- **Formato**: `[YYYY-MM-DD HH:MM:SS] LEVEL - logger:function:line - message`

### Níveis de Log
- `DEBUG` - Informações detalhadas (arquivo apenas)
- `INFO` - Eventos importantes (arquivo + UI)
- `WARNING` - Avisos
- `ERROR` - Erros

---

## ⚡ Performance

### Cache Inteligente
- Branches são cacheadas por **5 segundos**
- Reduz chamadas desnecessárias ao Git
- Cache é limpo automaticamente entre operações críticas

### Threading
- Operações longas rodam em thread separada
- UI não congela durante git commands
- Feedback visual em tempo real

---

## 🔄 CI/CD Pipeline

Automação via GitHub Actions:
- ✅ Testes em múltiplas versões Python (3.10, 3.11, 3.12, 3.13)
- 📋 Linting com flake8
- 🎨 Formatação com black
- 🛡️ Verificação de segurança com bandit
- 📦 Verificação de dependências vulneráveis

---

## 🚨 Tratamento de Erros

### Validações
- ✅ Repositório válido (contém `.git/`)
- ✅ Entrada do usuário não vazia
- ✅ Alterações locais antes de checkout
- ✅ PR existe antes de mergear

### Exceções Customizadas
- `GitCommandError` - Erro em comando Git
- `EnvironmentError` - Token GitHub não encontrado

---

## 📝 Variáveis de Ambiente

### `.env` (criar manualmente)
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEBUG=0  # opcional
```

---

## 🧪 Requisitos

- Python **3.10+**
- Git instalado (`git --version`)
- pip/pipenv para gerenciamento de dependências

---

## 📌 Melhorias Implementadas Recentemente

✨ **Fase 1 - Critical Fixes**
- ✅ Corrigido local de `pr_operations.py` (core → services)
- ✅ Removido `tk==0.1.0` desnecessário
- ✅ Validação de repositório Git ao selecionar
- ✅ Corrigido tipo de exceção em `get_default_main_branch()`

✨ **Fase 2 - Important**
- ✅ Sistema de logging estruturado com arquivo rotativo
- ✅ Validação de entrada em popups
- ✅ `.gitignore` reforçado com padrões de segurança
- ✅ Logging em todos os serviços

✨ **Fase 3 - UX Improvements**
- ✅ Cache inteligente com TTL (5s) para branches
- ✅ Threading para operações não bloqueantes
- ✅ Feedback visual durante operações longas
- ✅ Worker thread reutilizável

✨ **Fase 4 - Robustez**
- ✅ Testes unitários com pytest
- ✅ CI/CD com GitHub Actions
- ✅ Fixtures compartilhadas
- ✅ Code quality (flake8, black, pylint)

---

## 🙋‍♂️ Suporte

Caso tenha dúvidas, sugestões ou queira contribuir com melhorias, fale com:

- 📧 jean.heberth@example.com
- 🐙 [GitHub Issues](https://github.com/JeanHeberth/automatizarBranch/issues)
- 🔀 [Pull Requests](https://github.com/JeanHeberth/automatizarBranch/pulls)

---

## ✍️ Autor

**Jean Heberth Souza Vieira dos Santos**
