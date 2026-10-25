
pipeline {
    agent any
    parameters {
        choice(
            name: 'Action',
            choices: 'apply\ndestroy',
            description: 'Apply or Destroy Instance'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'docker-hub-credentials',
                                    usernameVariable: 'DOCKER_USER',
                                    passwordVariable: 'DOCKER_PASSWORD')
                ])

                 {
                    script {
                        if (params.Action == 'apply') {
                            sh 'ansible-playbook infra/ansible/build-docker.yaml'
                        }
                    }
                }
            }
        }

        stage('Terraform') {
            steps {
                script {
                    if (params.Action == 'apply') {
                        sh 'terraform -chdir=infra/terraform init'
                        sh 'terraform -chdir=infra/terraform apply -var="name=prod-ict381" -var="group=web" --auto-approve'
                    }
                    else {
                        sh 'terraform -chdir=infra/terraform destroy -var="name=prod-ict381" -var="group=web" --auto-approve'
                    }
                }
            }
        }

        stage('Ansible') {
            steps {
                script {
                    if (params.Action == 'apply') {
                        sh 'ansible-playbook -i /etc/ansible/aws_ec2.yaml infra/ansible/prod-application.yaml'
                    }
                }
            }
        }
    }
}
