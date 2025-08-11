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

- Interface simples em Tkinter
- Operações Git automatizadas
- Dropdowns interativos para seleção de branches
- Logs com timestamp salvos em `git_automation.log`
- Número do PR mostrado automaticamente após criação, facilitando o merge

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
   .venv\Scripts\activate       # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Execução

```bash
python main.py
```

---

## 🖥️ Como usar

1. Clique em **Selecionar Repositório** e escolha a pasta do seu projeto Git.
2. Use os botões da interface para:
    - Criar uma nova branch `feature/<nome>`
    - Fazer commit e/ou push das alterações
    - Atualizar a branch principal (main/master)
    - **Trocar de branch (checkout)** via dropdown
    - **Deletar branch local** com segurança (não pode ser a branch atual)
    - **Criar Pull Request automaticamente para a branch atual**
    - **Merge automático após criação do PR** (se possível)
    - **Merge manual do PR** (caso necessário, com uso do número do PR)
3. Os logs dos comandos executados aparecerão na parte inferior da janela.
4. Todas as saídas também são salvas em `git_automation.log`.

---

## 🔁 Como obter o número do Pull Request (PR)

Ao criar um PR pela automação:

- O número do PR (ex: `#45`) será mostrado automaticamente no log logo após a criação.
- Esse número também está disponível no GitHub:
    - Vá até a aba **Pull requests** do seu repositório.
    - Localize seu PR e verifique o número no início do título ou na URL.

Você pode usar esse número para realizar merge manual com o botão **Merge Pull Request**, caso o merge automático não aconteça.

> ⚠️ Certifique-se de que o PR esteja "mergeable" (sem conflitos) antes de tentar mergear via automação.

---

## 📂 Estrutura

```
.
├── main.py
├── gui.py
├── utils.py
├── git_operations.py
├── interface_widgets.py
├── requirements.txt
├── .gitignore
├── git_automation.log  # (gerado automaticamente)
└── README.md
```

---

## 🧪 Requisitos

- Python 3.11+
- Git instalado e disponível no terminal (`git --version`)

---

## 📌 Sugestões de Melhoria Futuras

- Suporte para autenticação com SSH.
- Integração com plataformas como GitLab ou Bitbucket.
- Histórico visual de merges realizados.
- Integração com Jira para vincular branches a tarefas automaticamente.
- Suporte a múltiplos repositórios Git simultâneos.
- Exportação de logs em PDF diretamente da interface.

---

## 🙋‍♂️ Suporte

Caso tenha dúvidas, sugestões ou queira contribuir com melhorias, fique à vontade para abrir uma [issue](https://github.com/JeanHeberth/automatizarBranch/issues) ou um [pull request](https://github.com/JeanHeberth/automatizarBranch/pulls).

---

## ✍️ Autor

Jean Heberth Souza Vieira dos Santos
