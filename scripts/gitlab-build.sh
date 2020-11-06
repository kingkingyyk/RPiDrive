cd backend/
rm -Rf static/drive
rm RPiDrive_ng/settings/dev.py
rm RPiDrive_ng/settings/prod.py
cd ../frontend
npm install @angular/cli -g
npm install
ng build --prod --aot --deployUrl=/static/drive/ --outputPath=../backend/static/drive/
cd ../backend
mv -f static/drive/index.html drive/templates/drive/index.html
cd ../
mv backend build