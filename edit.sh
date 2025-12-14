#! /bin/bash

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <table> <slug>"
    exit 1
fi

sqlite3 knowledge.db "SELECT html FROM \"$1\" WHERE slug='$2';" > buf.html

vi -c "set backupcopy=yes" buf.html

sqlite3 knowledge.db "UPDATE \"$1\" SET html=CAST(readfile('buf.html') as TEXT) WHERE slug='$2';"

python3 main.py

if [[ "$(uname -s)" == "Darwin" ]]; then
    open "dist/$1/$2.html"
fi
