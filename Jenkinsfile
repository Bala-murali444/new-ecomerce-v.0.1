pipeline {
  environment {
    registry = "9885614249/ecom-app"
    registryCredential = 'docker-hub-ecom'
    dockerImage = ''
  }
  agent any
  stages {
    stage('Cloning Git') {
      steps {
        git 'https://github.com/Bala-murali444/new-ecomerce-v.0.1.git'
      }
    }
    stage('Building image') {
      steps{
        script {
            dockerImage = docker.build registry + ":$BUILD_NUMBER"  
        }
      }
    }
    stage('Deploy Image') {
      steps{
        script {
          docker.withRegistry( '', registryCredential ) {
            dockerImage.push()
          }
        }
      }
    }
    stage('Remove Unused docker image') {
      steps{
        sh "docker rmi $registry:$BUILD_NUMBER"
      }
    }
  }
}