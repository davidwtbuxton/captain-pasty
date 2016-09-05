LIBS="libs"

npm install
rm -rf "$LIBS"
pip install --target "$LIBS" --requirement requirements.txt
