pipeline {
    agent any

    environment {
        DOCKER_USER     = "verventech"
        VM_USER         = "verjenkins"
        STAGING_IP      = "192.168.1.99"
        PROD_IP         = "192.168.1.100"
        DOCKER_CREDS_ID = "docker-hub-pat"
        SSH_CREDS_ID    = "vm-ssh-key"
        TAG             = "${env.BUILD_NUMBER}"
        APP_NAME        = "blog-web-app"
    }

    stages {
        stage('Secret Scan') {
            steps {
                sh """
                    docker run --rm -v "\${WORKSPACE}":/repo \
                      ghcr.io/gitleaks/gitleaks:v8.30.1 \
                      dir --redact --no-banner /repo
                """
            }
        }

        stage('Unit Tests & Linting') {
            steps {
                sh """
                    docker run --rm -v "\${WORKSPACE}/backend":/app -w /app python:3.11-slim bash -c '
                        pip install -q -r requirements-test.txt &&
                        ruff check --select E4,E7,E9,F routes main.py db.py models.py security.py tests &&
                        PYTHONPATH=/app pytest tests/unit -v --junitxml=unit-results.xml
                    '
                """
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'backend/unit-results.xml'
                }
            }
        }

        stage('Integration Tests') {
            steps {
                script {
                    def netName = "ci-net-${TAG}"
                    def dbName = "ci-db-${TAG}"
                    try {
                        sh """
                            docker network create ${netName}
                            docker run -d --name ${dbName} --network ${netName} \
                              --health-cmd "pg_isready -U postgres -d test_db" \
                              --health-interval 2s --health-timeout 2s --health-retries 30 \
                              -e POSTGRES_USER=postgres \
                              -e POSTGRES_HOST_AUTH_METHOD=trust \
                              -e POSTGRES_DB=test_db \
                              postgres:16-alpine
                        """
                        timeout(time: 2, unit: 'MINUTES') {
                            sh """
                                docker run --rm --network ${netName} postgres:16-alpine \
                                  sh -c "until pg_isready -h ${dbName} -U postgres -d test_db; do sleep 1; done"
                            """
                        }
                        sh """
                            docker run --rm --network ${netName} \
                              -v "\${WORKSPACE}/backend":/app -w /app \
                              -e PYTHONPATH=/app \
                              -e DATABASE_URL=postgresql://postgres@${dbName}:5432/test_db \
                              python:3.11-slim bash -c '
                                pip install -q -r requirements-test.txt &&
                                pytest tests/integration -v --junitxml=integration-results.xml
                              '
                        """
                    } finally {
                        sh "docker rm -f ${dbName} || true"
                        sh "docker network rm ${netName} || true"
                    }
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'backend/integration-results.xml'
                }
            }
        }

        stage('Build Images') {
            steps {
                sh "docker build -t ${DOCKER_USER}/${APP_NAME}-backend:v${TAG} -f backend/Dockerfile backend"
                sh "docker build -t ${DOCKER_USER}/${APP_NAME}-frontend:v${TAG} -f frontend/Dockerfile frontend"
            }
        }

        stage('Push Images') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: DOCKER_CREDS_ID,
                        passwordVariable: 'DOCKER_PASS',
                        usernameVariable: 'DOCKER_LOGIN'
                    )]) {
                        sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_LOGIN" --password-stdin'
                        sh "docker push ${DOCKER_USER}/${APP_NAME}-backend:v${TAG}"
                        sh "docker push ${DOCKER_USER}/${APP_NAME}-frontend:v${TAG}"
                        sh 'docker logout'
                    }
                }
            }
        }

        stage('Create Environment File') {
            steps {
                withCredentials([
                    string(credentialsId: 'blog-app-db-password', variable: 'DB_PASS'),
                    string(credentialsId: 'blog-app-secret-key', variable: 'APP_SECRET')
                ]) {
                    sh '''
                        umask 077
                        cat > .env <<EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_DB=blog_app
POSTGRES_HOST=db
POSTGRES_PORT=5432
SECRET_KEY=$APP_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GATEWAY_PORT=8081
EOF
                    '''
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                sshagent([SSH_CREDS_ID]) {
                    // Remove any broken gateway directory auto-created by Docker before copying fresh files
                    sh "ssh -o StrictHostKeyChecking=no ${VM_USER}@${STAGING_IP} 'rm -rf ~/${APP_NAME}/gateway && mkdir -p ~/${APP_NAME}'"
                    sh "scp -r -o StrictHostKeyChecking=no docker-compose.yml .env db gateway ${VM_USER}@${STAGING_IP}:~/${APP_NAME}/"
                    sh """
                        ssh -o StrictHostKeyChecking=no ${VM_USER}@${STAGING_IP} '
                            cd ~/${APP_NAME}
                            export TAG=${TAG}
                            export DOCKER_USER=${DOCKER_USER}
                            docker compose -p ${APP_NAME} pull
                            docker compose -p ${APP_NAME} up -d --force-recreate --remove-orphans
                        '
                    """
                }
            }
        }

        stage('Staging Smoke & Health Test') {
            steps {
                sh """
                    # 1. Verify React frontend is served by Nginx (200 OK)
                    curl --fail --silent --show-error --retry 5 --retry-delay 2 \
                      http://${STAGING_IP}:8081/ > /dev/null

                    # 2. Verify FastAPI backend is alive
                    curl --fail --silent --show-error --retry 5 --retry-delay 2 \
                      http://${STAGING_IP}:8081/api/health

                    # 3. Verify FastAPI can query PostgreSQL
                    curl --fail --silent --show-error \
                      "http://${STAGING_IP}:8081/api/blogs?limit=1" > /dev/null
                """
            }
        }

        stage('Approval Gate') {
            steps {
                input message: "Automated tests passed! Verify Staging at http://${STAGING_IP}:8081. Promote to Production?", ok: "Deploy!"
            }
        }

        stage('Deploy to Production') {
            steps {
                sshagent([SSH_CREDS_ID]) {
                    sh "ssh -o StrictHostKeyChecking=no ${VM_USER}@${PROD_IP} 'rm -rf ~/${APP_NAME}/gateway && mkdir -p ~/${APP_NAME}'"
                    sh "scp -r -o StrictHostKeyChecking=no docker-compose.yml .env db gateway ${VM_USER}@${PROD_IP}:~/${APP_NAME}/"
                    sh """
                        ssh -o StrictHostKeyChecking=no ${VM_USER}@${PROD_IP} '
                            cd ~/${APP_NAME}
                            export TAG=${TAG}
                            export DOCKER_USER=${DOCKER_USER}
                            docker compose -p ${APP_NAME} pull
                            docker compose -p ${APP_NAME} up -d --force-recreate --remove-orphans
                        '
                    """
                }
            }
        }
    }

    post {
        always {
            sh 'rm -f .env'
        }
    }
}