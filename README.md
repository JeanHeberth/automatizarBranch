# 🧠 Automação Git com Tkinter

Aplicativo com interface gráfica em Tkinter para facilitar ações Git como:

- Seleção de repositório
- Criação de branches (feature/)
- Commit e push
- Atualização da branch principal (`main` ou `master`)
- **Checkout de branches existentes**
- **Exclusão (delete) de branches locais**
- Visualização de logs dos comandos executados

---

## ✅ Funcionalidades

- Interface simples em Tkinter
- Operações Git automatizadas
- Dropdowns interativos para seleção de branches
- Logs com timestamp salvos em `git_automation.log`

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
3. Os logs dos comandos executados aparecerão na parte inferior da janela.
4. Todas as saídas também são salvas em `git_automation.log`.

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

## ✍️ Autor

Jean Heberth Souza Vieira dos Santos