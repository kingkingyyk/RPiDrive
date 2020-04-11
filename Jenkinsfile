pipeline {
    agent {
        label 'slave'
    }

    stages {
        stage('Build') {
            steps {
                sh 'build.sh'
            }
        }
        stage('Release') {
            steps {
                githubrelease 'asset kingkingyyk/RPiDrive upload develop-latest build.tar.gz'
            }
        }
    }

}