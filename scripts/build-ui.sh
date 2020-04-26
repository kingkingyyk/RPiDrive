cd ..
cd frontend/
sudo npm install @angular/cli -g
npm install
ng build --prod --aot --deployUrl=/static/drive/ --outputPath=../backend/static/drive/
cd ../backend
mv static/drive/index.html drive/templates/drive/
rm RPiDrive_ng/settings/dev.py
tar -czvf build.tar.gz *
mv build.tar.gz ../
cd ..
tar -czvf build.tar.gz backend/* dockerfile