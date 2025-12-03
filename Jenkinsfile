pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.12'
        VENV_DIR = '.venv'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code...'
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment...'
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Lint Code') {
            steps {
                echo '🔍 Linting Python code...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip install pylint flake8
                    pylint BeatWake-SourceCode.py spotify_auth.py || true
                    flake8 BeatWake-SourceCode.py spotify_auth.py || true
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Running tests...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    # Add your test commands here when you have tests
                    echo "No tests configured yet"
                '''
            }
        }
        
        stage('Security Scan') {
            steps {
                echo '🔒 Running security scan...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pip install safety bandit
                    safety check || true
                    bandit -r . -f json -o bandit-report.json || true
                '''
            }
        }
        
        stage('Build Documentation') {
            steps {
                echo '📚 Building documentation...'
                sh '''
                    echo "README.md exists: $(test -f README.md && echo 'yes' || echo 'no')"
                '''
            }
        }
        
        stage('Package') {
            steps {
                echo '📦 Packaging application...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    # Create distribution package
                    mkdir -p dist
                    cp BeatWake-SourceCode.py dist/
                    cp spotify_auth.py dist/
                    cp requirements.txt dist/
                    cp README.md dist/
                    cd dist && tar -czf BeatWake-${BUILD_NUMBER}.tar.gz *
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
            archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
        }
        failure {
            echo '❌ Pipeline failed!'
        }
        always {
            echo '🧹 Cleaning up...'
            cleanWs()
        }
    }
}
