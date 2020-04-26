cd ..
cd frontend/
sudo npm install @angular/cli -g
npm install
ng build --prod --aot --deployUrl=/static/drive/ --outputPath=../backend/static/drive/