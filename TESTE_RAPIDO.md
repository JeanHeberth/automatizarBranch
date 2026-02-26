# 🧪 Guia Rápido de Teste

## 1. Rodar os Testes

```bash
cd /Users/jeanheberth/Documents/GitClone/DesenvolvimentoPython/automatizarBranch

# Rodar todos os testes
python -m pytest tests/ -v

# Resultado esperado: 22 passed ✅
```

## 2. Testar na Aplicação (UI)

```bash
# Abrir a aplicação
python main.py
```

### Teste Cenário 1: Criar Branch e Fazer PR

1. Clique em **"Selecionar Repositório"** → Escolha um repositório Git local
2. Clique em **"🌱 Criar Branch"** → Digite `feature/teste-rebase`
3. Faça uma alteração qualquer em um arquivo
4. Clique em **"💾 Commit + Push"** → Digite mensagem `primeira alteracao`
5. Clique em **"🔗 Criar Pull Request"**:
   - Base: `develop` (ou `main`)
   - Compare: `feature/teste-rebase`
   - Title: `Teste Rebase`
6. ✅ PR criado com sucesso

### Teste Cenário 2: Fazer Alterações Adicionais (O Grande Teste!)

7. Faça **outra alteração** em um arquivo
8. Clique em **"🔄 Atualizar Branch"**
   - Deve sincronizar com `develop` via rebase
   - Mensagem: `✅ Branch 'feature/teste-rebase' sincronizada com 'develop'.`
9. Clique em **"💾 Commit + Push"** → Digite `segunda alteracao`
   - Deve fazer push com `--force-with-lease` se necessário
10. Clique em **"🔗 Criar Pull Request"** novamente
    - Base: `develop`
    - Compare: `feature/teste-rebase`
    - Title: `Teste Rebase - Segunda Alteração`
11. ✅ **SEM CONFLITO!** (Antes: ❌ CONFLITO)

### Teste Cenário 3: Cleanup

12. Clique em **"✅ Merge Pull Request"** → Digite `1` (número do PR)
13. Clique em **"🚮 Deletar Branch Remota"** → Digite `feature/teste-rebase`
14. Clique em **"🗑️ Deletar Branch Local"** → Digite `feature/teste-rebase`

---

## 3. Verificar Logs

```bash
# Abrir arquivo de log
tail -f /Users/jeanheberth/Documents/GitClone/DesenvolvimentoPython/automatizarBranch/logs/git_automation.log

# Procurar por "rebase"
grep -i "rebase" /Users/jeanheberth/Documents/GitClone/DesenvolvimentoPython/automatizarBranch/logs/git_automation.log

# Procurar por "force-with-lease"
grep -i "force" /Users/jeanheberth/Documents/GitClone/DesenvolvimentoPython/automatizarBranch/logs/git_automation.log
```

---

## 4. Validar Comportamento

### ✅ Validação 1: Rebase está acontecendo?

```bash
# No log deve aparecer:
# "Sincronizando com 'origin/develop'..."
# "Branch 'feature/xxx' sincronizada com 'develop'."
```

### ✅ Validação 2: Force-with-lease está sendo usado?

```bash
# No log ou ao tentar push deve aparecer:
# "push ... --force-with-lease"
```

### ✅ Validação 3: Alterações locais são validadas?

Teste:
1. Fazer uma alteração sem commit
2. Clique em **"🔄 Atualizar Branch"**
3. Deve aparecer erro: **"⚠️ Existem alterações locais"**

---

## 5. Teste CLI (Programaticamente)

```python
from services.branch_service import create_branch, update_branch, list_branches
from services.commit_service import commit_and_push

repo = "/caminho/para/seu/repo"

# Criar branch
print(create_branch(repo, "feature/cli-test"))

# Listar branches (cache: 5s)
print(list_branches(repo))

# Fazer alteração + commit + push
# ... faça uma alteração em um arquivo ...
print(commit_and_push(repo, "CLI test commit"))

# Atualizar (rebase com develop)
print(update_branch(repo, "feature/cli-test"))

# Push novamente (com --force-with-lease se necessário)
print(commit_and_push(repo, "CLI test alteracao 2"))
```

---

## 6. Debugging

Se algo der errado:

```bash
# 1. Verificar logs
tail -100 /Users/jeanheberth/Documents/GitClone/DesenvolvimentoPython/automatizarBranch/logs/git_automation.log

# 2. Rodar testes novamente
python -m pytest tests/ -v -s

# 3. Verificar status do repo
cd /seu/repositorio
git status
git log --oneline -10

# 4. Verificar branch base
git rev-parse --verify origin/develop
git rev-parse --verify origin/main
git rev-parse --verify origin/master
```

---

## 📊 Checklist de Teste

- [ ] Testes unitários passam (22/22)
- [ ] Aplicação abre sem erros
- [ ] Criar branch funciona
- [ ] Commit + Push funciona
- [ ] Criar PR funciona
- [ ] Update branch sincroniza com develop
- [ ] Múltiplas alterações funcionam sem conflito
- [ ] Merge PR funciona
- [ ] Deletar branches locais/remotas funciona
- [ ] Logs mostram rebase acontecendo
- [ ] Alterações locais não commitadas são detectadas

---

## 🎯 Resultado Esperado

```
TESTE 1: Criar branch → PR ✅
TESTE 2: Alterar → Update → PR (SEM CONFLITO!) ✅
TESTE 3: Cleanup ✅

→ Sistema funcionando perfeitamente! ✅
```

---

## 🚨 Possíveis Erros

### Erro: "Already up to date."
- Normal! Significa que não há nada para rebase
- Continuar com o próximo passo

### Erro: "CONFLICT (content): Merge conflict in..."
- Rebase manual necessário
- Resolver conflitos manualmente no editor

### Erro: "Permission denied"
- Verificar token GitHub
- Executar: `gh auth login`

### Erro: "branch not found"
- Certificar que branch existe em origin
- Executar: `git fetch origin`

---

## 📞 Suporte

Dúvidas?
1. Leia `MELHORIAS.md` para entender as mudanças
2. Leia `VALIDACAO.md` para cenários testados
3. Verifique os logs em `/logs/git_automation.log`
4. Execute testes com `-v -s` para mais detalhes

