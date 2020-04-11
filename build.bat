cd frontend\ &&^
npm install &&^
ng build --prod --aot --deployUrl=/static/drive/ --outputPath=..\backend\static\drive\ &&^
cd ..\backend &&^
move /y static\drive\index.html drive\templates\drive
