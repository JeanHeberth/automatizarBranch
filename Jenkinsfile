pipeline {
    agent any

    environment {
        PYTHON_ENV = ".venv"
        APP_MAIN = "main.py"
        REQUIREMENTS = "requirements.txt"
        PYTHON_EXE = "python"  // ou "python3" se for o nome no PATH
    }

    stages {
        stage('📦 Preparar Ambiente') {
            steps {
                echo "🔧 Criando ambiente virtual..."
                bat """
                    if not exist %PYTHON_ENV% (
                        %PYTHON_EXE% -m venv %PYTHON_ENV%
                    )
                    call %PYTHON_ENV%\\Scripts\\activate
                    python -m pip install --upgrade pip
                    if exist %REQUIREMENTS% (
                        pip install -r %REQUIREMENTS%
                    )
                """
            }
        }

        stage('🧪 Testes Automatizados') {
            steps {
                echo "🧪 Executando testes..."
                bat """
                    call %PYTHON_ENV%\\Scripts\\activate
                    if exist tests (
                        pytest --maxfail=1 --disable-warnings -q
                    ) else (
                        echo Nenhum diretório de testes encontrado.
                    )
                """
            }
        }

        stage('🧹 Lint (Flake8)') {
            steps {
                echo "🧹 Verificando qualidade do código..."
                bat """
                    call %PYTHON_ENV%\\Scripts\\activate
                    pip install flake8
                    flake8 . --max-line-length=120 || echo "⚠️ Aviso: problemas de lint encontrados."
                """
            }
        }

        stage('🏗️ Build (Opcional)') {
            steps {
                echo "🏗️ Empacotando app..."
                bat """
                    call %PYTHON_ENV%\\Scripts\\activate
                    pip install pyinstaller
                    pyinstaller --onefile %APP_MAIN% --name AutomacaoGitTk
                """
            }
        }

        stage('✅ Finalização') {
            steps {
                echo "✅ Pipeline concluído com sucesso!"
            }
        }
    }

    post {
        success {
            echo "🎉 Tudo certo! Build e testes finalizados."
        }
        failure {
            echo "❌ Pipeline falhou. Verifique os logs acima."
        }
    }
}
