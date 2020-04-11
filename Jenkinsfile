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
                sh '/home/lel/.local/bin/githubrelease asset kingkingyyk/RPiDrive upload $BRANCH_NAME-$BUILD_ID build.tar.gz'
            }
        }
    }

}