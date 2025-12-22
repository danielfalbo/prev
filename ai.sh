#!/bin/bash

FILES=(
  "README"

  "main.py"
  "create.sql"

  "components/list.html"
  "components/dateage.html"

  "edit.sh"

  "templates/global.css"

  "templates/index.html"
  "templates/notes.html"
  "templates/authors.html"
  "templates/resources.html"

  "vercel.json"
)

TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

{
  echo "I am currently working on my personal website."
  echo "It's a custom-made vanilla SSG using Python and SQLite."
  echo ""

  for FILE_PATH in "${FILES[@]}"; do
    echo "Here's $FILE_PATH:"
    echo ""
    cat "$FILE_PATH"
    echo -e "\n--- End of $FILE_PATH ---\n"
    echo ""
  done

  echo -e "\n--- End of Files ---\n"
} > "$TEMP_FILE"

cat "$TEMP_FILE" | pbcopy
echo "Success: Content of ${#FILES[@]} files copied to clipboard."
