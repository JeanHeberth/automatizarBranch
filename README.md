# 🧠 Automação Git com Tkinter

Aplicativo com interface gráfica em Tkinter para facilitar ações Git como:

- Seleção de repositório
- Criação de branches (feature/)
- Commit e push
- Atualização da branch principal (`main` ou `master`)
- Visualização de logs dos comandos executados

## ✅ Funcionalidades
- Interface simples em Tkinter
- Operações Git automatizadas
- Logs com timestamp salvos em `git_automation.log`

## 🛠️ Instalação

1. Clone o repositório:
   ```bash
   git clone  https://github.com/JeanHeberth/automatizarBranch.git
   cd seu-repo

2. Crie o ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Execução

```bash
python main.py
```

## 📂 Estrutura

```
.
├── main.py
├── gui.py
├── utils.py
├── git_operations.py
├── requirements.txt
├── .gitignore
├── git_automation.log  # (gerado automaticamente)
└── README.md
```

## 🧪 Requisitos

- Python 3.11+
- Git instalado e configurado

## ✍️ Autor

Jean Heberth Souza Vieira dos Santos