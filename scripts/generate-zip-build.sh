cd ../backend
mv static/drive/index.html drive/templates/drive/
rm RPiDrive_ng/settings/dev.py
tar -czvf build.tar.gz *
mv build.tar.gz ../
cd ..
tar -czvf build.tar.gz backend/* dockerfile