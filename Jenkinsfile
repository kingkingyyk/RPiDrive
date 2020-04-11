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
                sh '/home/lel/.local/bin/githubrelease release kingkingyyk/RPiDrive create $GIT_BRANCH-$BUILD_ID --prerelease'
                sh '/home/lel/.local/bin/githubrelease asset kingkingyyk/RPiDrive upload $GIT_BRANCH-$BUILD_ID build.tar.gz'
            }
        }
    }

}