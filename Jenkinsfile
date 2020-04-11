pipeline {
    agent {
        label 'slave'
    }

    stages {
        stage('Build') {
            steps {
                sh 'sh ./build.sh'
            }
        }
        stage('Release') {
            steps {
                sh '/home/lel/.local/bin/githubrelease asset kingkingyyk/RPiDrive upload develop-latest build.tar.gz'
            }
        }
    }

}