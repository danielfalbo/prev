#! /bin/bash

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <table> <slug>"
    exit 1
fi

TABLE="$1"
SLUG="$2"
DB="knowledge.db"
BUF='buf.html'

# ==========================================
# 1. Create Entry on DB if Missing.
# ==========================================

# Check if entry already exists.
EXISTS=$(sqlite3 $DB "SELECT count(*) FROM \"$TABLE\" WHERE slug='$SLUG';")

if [ "$EXISTS" -eq "0" ]; then
  echo "Entry '$SLUG' not found in '$TABLE'. Creating new..."

  # Handle Schema differences: 'authors' table uses 'name', others use 'title'.
  if [ "$TABLE" == "authors" ]; then
    read -p "Enter Name: " DISPLAY_VAL
    COL="name"
  else
    read -p "Enter Title: " DISPLAY_VAL
    COL="title"
  fi

  # Insert the new row with empty HTML.
  sqlite3 $DB "INSERT INTO \"$TABLE\" (slug, $COL, html) VALUES ('$SLUG', '$DISPLAY_VAL', '');"
fi

# ==========================================
# Fault-tolerant Buffer File Management.
# ==========================================

# Check if buf.html exists and is not empty.
if [ -s "$BUF" ]; then
  echo "----------------------------------------------------"
  echo "WARNING: '$BUF' is not empty!"
  echo "This might contain unsaved work from a previous session."
  echo "----------------------------------------------------"
  read -p "Load from local buffer instead of DB? [y/N]: " CHOICE

  if [[ "$CHOICE" =~ ^[Yy]$ ]]; then
    echo "Using local '$BUF' content..."
  else
    echo "Overwriting '$BUF' with fresh content from DB..."
    sqlite3 $DB "SELECT html FROM \"$TABLE\" WHERE slug='$SLUG';" > "$BUF"
  fi
else
  # File is empty or missing, safe to pull from DB
  sqlite3 $DB "SELECT html FROM \"$TABLE\" WHERE slug='$SLUG';" > "$BUF"
fi

# ==========================================
# 3. Editing.
# ==========================================

# Open vim for editing of the html content.
#
# 'backupcopy=yes' writes the actual original file at every ':w'
# so '--watch' mode can directly listen for changes on that file
# for the live preview feature (see README).
vi -c "set backupcopy=yes" "$BUF"

# ==========================================
# 4. Save and Cleanup.
# ==========================================

# Attempt to write updated html content back to DB.
# Note: 'set -e' ensures script exits here if sqlite3 fails.
sqlite3 $DB "UPDATE \"$TABLE\" SET html=CAST(readfile('$BUF') as TEXT) WHERE slug='$SLUG';"

# If we reached this line, the DB update was successful.
# Clean the buffer so the next run pulls fresh from DB.
> "$BUF"

echo "Database updated and buffer cleaned."

# ==========================================
# 5. Rebuild and Preview.
# ==========================================

# Rebuild site
python3 main.py

# Open edited page in browser (using macOS 'open')
if [[ "$(uname -s)" == "Darwin" ]]; then
  open "dist/$TABLE/$SLUG.html"
fi
