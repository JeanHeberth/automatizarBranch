pipeline {
    agent any

    environment {
        // Nome do ambiente virtual
        VENV = ".venv"
    }

    tools {
        python 'Python3'  // Nome configurado no Jenkins (Gerenciar Jenkins → Ferramentas)
    }

    stages {

        // =========================================================
        // 1️⃣ CHECKOUT
        // =========================================================
        stage('Checkout') {
            steps {
                echo "🔄 Clonando repositório..."
                checkout scm
            }
        }

        // =========================================================
        // 2️⃣ CONFIGURAR AMBIENTE
        // =========================================================
        stage('Setup Environment') {
            steps {
                script {
                    echo "⚙️ Criando ambiente virtual..."
                    if (isUnix()) {
                        sh "python3 -m venv ${VENV}"
                        sh ". ${VENV}/bin/activate && pip install --upgrade pip"
                        sh ". ${VENV}/bin/activate && pip install -r requirements.txt"
                    } else {
                        bat "python -m venv %VENV%"
                        bat "call %VENV%\\Scripts\\activate && pip install --upgrade pip"
                        bat "call %VENV%\\Scripts\\activate && pip install -r requirements.txt"
                    }
                }
            }
        }

        // =========================================================
        // 3️⃣ LINT E ANÁLISE ESTÁTICA
        // =========================================================
        stage('Lint & Code Quality') {
            steps {
                script {
                    echo "🔍 Verificando qualidade do código com flake8..."
                    if (isUnix()) {
                        sh ". ${VENV}/bin/activate && flake8 src tests"
                    } else {
                        bat "call %VENV%\\Scripts\\activate && flake8 src tests"
                    }
                }
            }
        }

        // =========================================================
        // 4️⃣ TESTES UNITÁRIOS
        // =========================================================
        stage('Run Tests') {
            steps {
                script {
                    echo "🧪 Executando testes com pytest..."
                    if (isUnix()) {
                        sh ". ${VENV}/bin/activate && pytest --maxfail=1 --disable-warnings -q --junitxml=reports/tests/test-results.xml --cov=src --cov-report=xml:reports/coverage.xml"
                    } else {
                        bat "call %VENV%\\Scripts\\activate && pytest --maxfail=1 --disable-warnings -q --junitxml=reports/tests/test-results.xml --cov=src --cov-report=xml:reports/coverage.xml"
                    }
                }
            }
            post {
                always {
                    junit 'reports/tests/test-results.xml'
                    publishHTML(target: [
                        reportDir: 'reports/tests',
                        reportFiles: 'test-results.xml',
                        reportName: 'Test Results'
                    ])
                }
            }
        }

        // =========================================================
        // 5️⃣ RELATÓRIO DE COBERTURA
        // =========================================================
        stage('Coverage Report') {
            steps {
                script {
                    echo "📊 Gerando relatório de cobertura..."
                    if (isUnix()) {
                        sh ". ${VENV}/bin/activate && coverage report -m"
                    } else {
                        bat "call %VENV%\\Scripts\\activate && coverage report -m"
                    }
                }
            }
        }

        // =========================================================
        // 6️⃣ DEPLOY (opcional)
        // =========================================================
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo "🚀 Deploy do app Python (exemplo)..."
                // Aqui poderia rodar: sh 'python app.py' ou docker build/push
            }
        }
    }

    // =========================================================
    // 🔄 POST ACTIONS (sempre executadas)
    // =========================================================
    post {
        always {
            echo '✅ Pipeline concluído.'
        }
        success {
            echo '🎉 Tudo certo! Testes e lint OK.'
        }
        failure {
            echo '❌ Falha detectada. Verifique o log do Blue Ocean 🚨'
        }
    }
}
