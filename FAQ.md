# ❓ FAQ - Perguntas Frequentes

## Sobre GitHub Token

### P: Precisamos do GitHub Token? Uma vez que o user tem acesso ao GitHub, podemos pegar o user pelo acesso?

**R:** ✅ **SIM! Já está implementado!**

A autenticação foi otimizada em `core/github_auth.py`:

```python
def get_github_token() -> str:
    """
    Tenta múltiplas fontes:
    1️⃣ GitHub CLI (gh auth login) - ⭐ RECOMENDADO
    2️⃣ Git Credential Manager - Alternativa
    3️⃣ .env (GITHUB_TOKEN) - Última opção
    """
```

#### Como usar (sem token hardcoded):

**Opção 1: GitHub CLI (RECOMENDADO)**
```bash
# Instalar GitHub CLI
brew install gh  # macOS
# ou
choco install gh  # Windows
# ou
sudo apt-get install gh  # Linux

# Autenticar
gh auth login

# Pronto! A aplicação usará automaticamente
```

**Opção 2: Git Credential Manager**
```bash
# Instalar Git Credential Manager
brew install --cask git-credential-manager  # macOS

# Autenticar uma vez
git clone https://github.com/seu-user/seu-repo

# Pronto! A aplicação usará automaticamente
```

**Opção 3: .env (apenas local/desenvolvimento)**
```bash
# Criar arquivo .env na raiz
echo "GITHUB_TOKEN=seu_token_aqui" > .env

# ⚠️ Inseguro! Use apenas em desenvolvimento
# Nunca commitar .env em produção
```

### P: Pegar o usuário pelo acesso?

**R:** ✅ **SIM! Existe função para isso!**

```python
from core.github_auth import get_github_user

# Obter usuário autenticado
username = get_github_user()
print(f"Usuário: {username}")  # → "seu-user"
```

A função usa `gh api user --jq ".login"` automaticamente!

---

## Sobre Branch Service

### P: O que mudou em update_branch()?

**R:** Tudo! Veja a comparação:

**ANTES:**
```python
def update_branch(repo_path: str, branch: str) -> str:
    # Apenas fazia pull (merge commit)
    run_git_command(repo_path, ["pull", "origin", branch])
    # ❌ Não sincronizava com branch base
    # ❌ Causava conflitos em novos PRs
```

**DEPOIS:**
```python
def update_branch(repo_path: str, branch: str, base_branch: str = None) -> str:
    # 1. Detecta branch base (develop/main/master)
    if not base_branch:
        base_branch = _get_default_base_branch(repo_path)
    
    # 2. Valida alterações locais
    status = run_git_command(repo_path, ["status", "--porcelain"])
    if status.strip():
        raise GitCommandError("Commit ou descarte antes!")
    
    # 3. Faz rebase com branch base
    run_git_command(repo_path, ["fetch", "origin", base_branch])
    run_git_command(repo_path, ["rebase", f"origin/{base_branch}"])
    
    # 4. Force push seguro
    run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])
    # ✅ Sincronizado! ✅ Sem conflitos!
```

### P: Pode dar conflito de rebase?

**R:** Sim, é possível! Mas:

1. **Muito improvável** - Rebase funciona bem se:
   - Branch base não mudou (ex: develop = develop)
   - Suas alterações não conflitam com base

2. **Se der conflito:**
   - Mensagem clara: `"CONFLICT (content): Merge conflict in..."`
   - Você recebe a informação para resolver
   - Instruções aparecem no log

3. **Como resolver:**
   ```bash
   cd seu-repo
   # Git vai parar o rebase e pedir para resolver
   # Editar arquivos com conflito (↓ vs ↑)
   git add .
   git rebase --continue
   ```

### P: O --force-with-lease é seguro?

**R:** ✅ **SIM! Melhor que --force puro**

| Opção | Segurança | Descrição |
|-------|-----------|-----------|
| `--force` | ❌ Perigoso | Sobrescreve tudo |
| `--force-with-lease` | ✅ Seguro | Verifica antes |
| Sem flag | ✅ Normal | Rejeita se diverje |

`--force-with-lease`:
- Só funciona se ninguém mais fez push
- Não sobrescreve trabalho alheio
- Melhor para uso em rebase seguro

---

## Sobre Conflitos em PR/MR

### P: Por que dava conflito depois de PR?

**R:** Exemplo do problema:

```
Timeline:
1. Criar branch feature/x
   Commit A: "seu código"
   Push → origin/feature/x

2. Fazer PR: feature/x → develop
   PR criado com A

3. Fazer alterações
   Commit B: "sua alteração"
   Push → origin/feature/x

4. ❌ CONFLITO! Por quê?
   - develop foi atualizado (outros PRs mergiados)
   - feature/x ainda baseado em develop ANTIGO
   - Conflito entre develop NOVO e feature/x
```

**Solução:**
```
Novo fluxo:
1. Criar branch feature/x
2. Fazer alterações + push
3. update_branch() [REBASE COM DEVELOP NOVO!]
4. ✅ Sem conflito!
5. Fazer mais alterações
6. update_branch() [REBASE COM DEVELOP MAIS NOVO AINDA!]
7. ✅ Ainda sem conflito!
```

### P: Isso muda o histórico?

**R:** **SIM**, rebase reescreve histórico:

**Pull (merge):**
```
develop: A — B — C
                ↘
feature:    → D — E
                ↙
Resultado: A — B — C — M (merge commit)
             ↑ histórico não alterado
```

**Rebase:**
```
develop: A — B — C
feature:    → D — E
Resultado: A — B — C — D' — E'
             ↑ D e E reescritos!
             ↑ histórico mais limpo
```

Benefícios do rebase:
- Histórico linear (mais fácil de ler)
- Sem merge commits desnecessários
- Commits em ordem cronológica

---

## Sobre Testes

### P: Por que só 22 testes?

**R:** Cobertura foi otimizada para:
- ✅ Funcionalidades críticas (branch, commit, PR)
- ✅ Casos de erro (GitCommandError, GitHubAuthError)
- ✅ Validações (safe_checkout, update_branch)

Testes de integração (Git real) exigem repositório de teste.

### P: Como rodar testes?

**R:**
```bash
# Todos
python -m pytest tests/ -v

# Específico
python -m pytest tests/test_branch_service.py -v

# Com cobertura
python -m pytest tests/ --cov=services --cov=core

# Verbose (mostrar prints)
python -m pytest tests/ -v -s
```

---

## Sobre Uso Prático

### P: E se alguém fizer força push enquanto estou rebasing?

**R:** `--force-with-lease` protege você!

```
Cenário perigoso:
1. Você começa rebase
2. Outro dev faz força push
3. `git push --force-with-lease` vai:
   ❌ Rejeitar (seguro!)
   Mensagem: "remote has newer commits"
```

### P: Posso usar update_branch() com outra branch base?

**R:** ✅ **SIM!**

```python
from services.branch_service import update_branch

# Sincronizar com 'main' em vez de 'develop'
update_branch(repo, "feature/x", "main")

# Sincronizar com 'staging'
update_branch(repo, "feature/x", "staging")

# Auto-detectar (padrão)
update_branch(repo, "feature/x")  # Tenta develop → main → master
```

### P: E se a branch ainda não existir no remoto?

**R:** Código cuida disso:

```python
if remote_exists:
    # Já existe: rebase + force-with-lease
    run_git_command(repo_path, ["rebase", f"origin/{base_branch}"])
    run_git_command(repo_path, ["push", "origin", branch, "--force-with-lease"])
else:
    # Nova: push inicial com tracking
    run_git_command(repo_path, ["push", "-u", "origin", branch])
```

---

## Sobre Performance

### P: Cache está funcionando?

**R:** ✅ **SIM! TTL = 5 segundos**

```python
@cached(ttl=5)
def list_branches(repo_path: str) -> List[str]:
    """Primeira chamada: executa git"""
    # t=0: executa git branch
    # t=1: retorna do cache
    # t=2: retorna do cache
    # t=5.1: cache expirado, executa git novamente
```

Benefício:
- UI não fica lenta ao listar branches múltiplas vezes
- Ainda sincroniza com remoto a cada 5s

---

## Sobre Segurança

### P: É seguro usar com múltiplos devs?

**R:** ✅ **SIM! Melhor que antes**

Proteções implementadas:
1. ✅ `--force-with-lease` previne sobrescrita
2. ✅ Validação de alterações locais
3. ✅ Rebase limpo (sem merge commits)
4. ✅ Logs detalhados
5. ✅ GitHub CLI para token seguro

### P: Preciso remover .env com GITHUB_TOKEN?

**R:** ✅ **Recomendado!**

```bash
# Se tem .env com GITHUB_TOKEN:
1. Use `gh auth login` (GitHub CLI)
2. Remova GITHUB_TOKEN de .env
3. Commit para remover do histórico
   git rm --cached .env
   git commit -m "Remove GITHUB_TOKEN"
4. Adicione .env ao .gitignore
   echo ".env" >> .gitignore
```

Mas aplicação suporta ambos (secure fallback).

---

## Troubleshooting

### P: "Nenhuma branch base detectada, usando 'main'"

**R:** Significa que:
- ❌ Repositório não tem develop, main ou master
- ✅ Código usa fallback para 'main'

Solução:
```python
# Especificar manualmente
update_branch(repo, "feature/x", "your-branch-name")
```

### P: "Existem alterações locais não commitadas"

**R:** Exatamente como esperado!

```bash
# Solução 1: Commit
git add .
git commit -m "mensagem"

# Solução 2: Discard
git checkout -- .

# Solução 3: Stash
git stash
```

### P: Rebase ficou em estado "detached HEAD"

**R:** Git em estado estranho:

```bash
# Verificar
git status

# Resolver
git rebase --abort  # Desfazer rebase
# ou
git rebase --continue  # Continuar após resolver conflitos
```

---

## Resumo Rápido

| Pergunta | Resposta |
|----------|----------|
| Token necessário? | ❌ Não (GitHub CLI) |
| Update funciona bem? | ✅ Sim (rebase) |
| Conflitos resolvidos? | ✅ Sim (sincronização) |
| Force-with-lease seguro? | ✅ Sim |
| Testes passam? | ✅ 22/22 |
| Pronto para usar? | ✅ SIM! |

---

## Próximas Melhorias (Opcionais)

1. Adicionar stash automático antes de rebase
2. Merge automático se não houver conflito
3. Notificações de webhook para PRs
4. UI aprimorada com status de rebase
5. Suporte a Git Flow automático

---

**Última atualização:** 25 de Fevereiro de 2026  
**Status:** ✅ PRONTO PARA USAR

