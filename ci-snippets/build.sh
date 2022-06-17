cd ../backend/
rm -Rf static/drive
cd ../frontend
npm install --global npm@6
npm install @angular/cli -g
npm install
ng build --aot --deploy-url=/drive/static/ --output-path=../backend/static/
cd ../backend
mv -f static/index.html drive/templates/drive/index.html
rm requirements-ci.txt
rm requirements-test.txt
rm pytest.ini
rm config.yaml.sample
rm config-test.yaml
rm docker-compose-dev.yaml
rm unit-test-badge.svg
mv docker-start.sh start.sh
cd ../
mv backend app
tar -czvf build.tar.gz app/*
