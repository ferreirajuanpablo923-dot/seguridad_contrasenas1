pipeline {
    agent any

    environment {
        APP_NAME = "seguridad_contrasenas"
        VERSION = "1.0.${BUILD_NUMBER}"
        VENV_DIR = "venv"
    }

    stages {
        stage('Preparar entorno') {
            steps {
                echo "Creando entorno virtual..."
                bat """
                python -m venv %VENV_DIR%
                call %VENV_DIR%\\Scripts\\activate
                pip install --upgrade pip
                pip install -r requirements.txt
                """
            }
        }

        stage('Compilar y empaquetar') {
            steps {
                echo "Empaquetando versión ${VERSION}..."
                bat """
                call %VENV_DIR%\\Scripts\\activate
                python setup.py sdist
                """
            }
        }

        stage('Guardar artefacto') {
            steps {
                archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
            }
        }
    }

    post {
        success {
            echo "✅ Build completado. Versión generada: ${VERSION}"
        }
        failure {
            echo "❌ Error en el proceso de build"
        }
    }
}
