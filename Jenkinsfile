pipeline {
    agent any

    environment {
        PYTHON_ENV = ".venv"
        APP_MAIN = "main.py"
        REQUIREMENTS = "requirements.txt"
    }

    stages {
        stage('📦 Preparar Ambiente') {
            steps {
                echo "Ativando ambiente virtual..."
                sh '''
                    if [ ! -d "$PYTHON_ENV" ]; then
                        python3 -m venv $PYTHON_ENV
                    fi
                    source $PYTHON_ENV/bin/activate
                    pip install --upgrade pip
                    if [ -f $REQUIREMENTS ]; then
                        pip install -r $REQUIREMENTS
                    fi
                '''
            }
        }

        stage('🧪 Executar Testes') {
            steps {
                echo "Executando testes automatizados..."
                sh '''
                    source $PYTHON_ENV/bin/activate
                    if [ -d "tests" ]; then
                        pytest --maxfail=1 --disable-warnings -q
                    else
                        echo "⚠️ Nenhum diretório de testes encontrado."
                    fi
                '''
            }
        }

        stage('🧹 Verificar Código') {
            steps {
                echo "Analisando qualidade do código (flake8)..."
                sh '''
                    source $PYTHON_ENV/bin/activate
                    pip install flake8
                    flake8 . --max-line-length=120 || true
                '''
            }
        }

        stage('🏗️ Build (Opcional)') {
            steps {
                echo "Empacotando app..."
                sh '''
                    source $PYTHON_ENV/bin/activate
                    pip install pyinstaller
                    pyinstaller --onefile $APP_MAIN --name "AutomacaoGitTk"
                '''
            }
        }

        stage('✅ Finalização') {
            steps {
                echo "Pipeline concluído com sucesso ✅"
            }
        }
    }

    post {
        failure {
            echo "❌ Pipeline falhou. Verifique os logs."
        }
        success {
            echo "🎉 Pipeline executado com sucesso!"
        }
    }
}
