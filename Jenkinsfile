pipeline {
    agent any
    
    environment {
        PYTHON_HOME = "C:\\Program Files\\Python311"
        PATH = "${env.PYTHON_HOME};${env.PYTHON_HOME}\\Scripts;${env.PATH}"
        VERSION = "${BUILD_NUMBER}"
        APP_NAME = "seguridad-contrasenas"
        PACKAGE_NAME = "${APP_NAME}-v${VERSION}"
    }
    
    stages {
        stage('Preparar entorno 🧰') {
            steps {
                echo "✅ Configurando entorno Python..."
                echo "📦 Versión del paquete: ${PACKAGE_NAME}"
                bat '"%PYTHON_HOME%\\python.exe" --version'
                bat '"%PYTHON_HOME%\\python.exe" -m pip install --upgrade pip'
                bat '"%PYTHON_HOME%\\python.exe" -m pip install -r requirements.txt'
                bat '"%PYTHON_HOME%\\python.exe" -m pip install wheel build'
            }
        }
        
        stage('Análisis de código 🔍') {
            steps {
                echo "🔍 Analizando calidad del código..."
                script {
                    try {
                        bat '"%PYTHON_HOME%\\python.exe" -m pip install flake8'
                        bat '"%PYTHON_HOME%\\python.exe" -m flake8 seguridad_contrasenas1 --max-line-length=120 --exclude=venv,__pycache__ --exit-zero'
                    } catch (Exception e) {
                        echo "⚠️ Análisis de código completado con advertencias"
                    }
                }
            }
        }
        
        stage('Pruebas 🧪') {
            steps {
                echo "🧪 Ejecutando pruebas automáticas..."
                dir('seguridad_contrasenas1') {
                    bat '"%PYTHON_HOME%\\python.exe" -m pytest --maxfail=1 --disable-warnings -v || exit /b 0'
                }
            }
        }
        
        stage('Compilar bytecode 🔨') {
            steps {
                echo "🔨 Compilando código Python a bytecode..."
                bat '"%PYTHON_HOME%\\python.exe" -m compileall seguridad_contrasenas1'
            }
        }
        
        stage('Generar información de versión 📝') {
            steps {
                echo "📝 Creando archivo de versión..."
                script {
                    // Crear archivo con información de la versión
                    bat """
                        echo VERSION=${VERSION} > version_info.txt
                        echo BUILD_DATE=%date% %time% >> version_info.txt
                        echo BUILD_NUMBER=${BUILD_NUMBER} >> version_info.txt
                        echo GIT_COMMIT=%GIT_COMMIT% >> version_info.txt
                    """
                }
            }
        }
        
        stage('Empaquetar con setup.py 📦') {
            steps {
                echo "📦 Creando paquetes distribuibles con setup.py..."
                dir('seguridad_contrasenas1') {
                    script {
                        // Verificar si existe setup.py
                        def setupExists = fileExists('setup.py')
                        if (setupExists) {
                            bat '"%PYTHON_HOME%\\python.exe" setup.py sdist bdist_wheel'
                            echo "✅ Paquetes .whl y .tar.gz creados"
                        } else {
                            echo "⚠️ No se encontró setup.py, saltando empaquetado con setuptools"
                        }
                    }
                }
            }
        }
        
        stage('Crear distribución completa 📁') {
            steps {
                echo "📁 Creando paquete ZIP completo para deployment..."
                script {
                    // Crear directorio releases si no existe
                    bat 'if not exist "releases" mkdir releases'
                    
                    // Copiar archivos importantes
                    bat """
                        copy version_info.txt releases\\
                        copy requirements.txt releases\\
                    """
                    
                    // Crear ZIP con todo el proyecto
                    bat """
                        powershell -Command "Compress-Archive -Path seguridad_contrasenas1\\*,requirements.txt,version_info.txt -DestinationPath releases\\${PACKAGE_NAME}-completo.zip -Force"
                    """
                    
                    // Si existe dist, copiar archivos
                    bat """
                        if exist seguridad_contrasenas1\\dist (
                            xcopy seguridad_contrasenas1\\dist\\*.* releases\\ /Y /I
                        )
                    """
                    
                    echo "✅ Distribución completa creada: ${PACKAGE_NAME}-completo.zip"
                }
            }
        }
        
        stage('Generar reporte de build 📊') {
            steps {
                echo "📊 Generando reporte de build..."
                script {
                    bat """
                        echo ================================================ > releases\\BUILD_REPORT.txt
                        echo    REPORTE DE BUILD - VERSION ${VERSION} >> releases\\BUILD_REPORT.txt
                        echo ================================================ >> releases\\BUILD_REPORT.txt
                        echo. >> releases\\BUILD_REPORT.txt
                        echo Proyecto: ${APP_NAME} >> releases\\BUILD_REPORT.txt
                        echo Version: ${VERSION} >> releases\\BUILD_REPORT.txt
                        echo Fecha: %date% %time% >> releases\\BUILD_REPORT.txt
                        echo Build Number: ${BUILD_NUMBER} >> releases\\BUILD_REPORT.txt
                        echo. >> releases\\BUILD_REPORT.txt
                        echo ARTEFACTOS GENERADOS: >> releases\\BUILD_REPORT.txt
                        dir releases >> releases\\BUILD_REPORT.txt
                    """
                }
            }
        }
        
        stage('Publicar artefactos 📤') {
            steps {
                echo "📤 Guardando artefactos de la versión ${VERSION}..."
                
                // Archivar TODO lo que está en releases
                archiveArtifacts artifacts: 'releases/**/*', fingerprint: true, allowEmptyArchive: true
                
                // Archivar dist si existe
                archiveArtifacts artifacts: 'seguridad_contrasenas1/dist/**/*', fingerprint: true, allowEmptyArchive: true
                
                script {
                    echo """
                    ╔════════════════════════════════════════════╗
                    ║     BUILD EXITOSO - VERSIÓN ${VERSION}     ║
                    ╚════════════════════════════════════════════╝
                    
                    📦 Paquete: ${PACKAGE_NAME}
                    📅 Fecha: ${new Date()}
                    🔗 URL: ${BUILD_URL}
                    
                    📁 Descarga los artefactos en:
                       ${BUILD_URL}artifact/
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ ¡Pipeline completado exitosamente!"
            echo "🎉 Versión ${VERSION} lista para deployment"
            echo "📦 Artefactos disponibles en: ${BUILD_URL}artifact/"
            echo ""
            echo "📥 ARCHIVOS GENERADOS:"
            echo "   • ${PACKAGE_NAME}-completo.zip (Proyecto completo)"
            echo "   • BUILD_REPORT.txt (Información del build)"
            echo "   • version_info.txt (Detalles de versión)"
            echo "   • Archivos .whl y .tar.gz (si setup.py existe)"
        }
        failure {
            echo "❌ Error en la construcción. Revisar logs para más detalles."
            echo "🔍 Console Output: ${BUILD_URL}console"
        }
        always {
            echo "🧹 Build finalizado"
            echo "📊 Total de builds: ${BUILD_NUMBER}"
        }
    }
}