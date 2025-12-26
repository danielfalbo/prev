#!/bin/bash

FILES=(
  "README"
  "main.py"
  "create.sql"
  "components/list.html"
  "components/dateage.html"
  "edit.sh"
  "ai.sh"
  "templates/404.html"
  "vercel.json"
)

# Check for --no-html flag
SKIP_HTML=false
if [[ "$1" == "--no-html" ]]; then
  SKIP_HTML=true
fi

TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

{
  echo "I am currently working on my personal website."
  echo "It's a custom-made vanilla SSG using Python and SQLite."
  echo ""

  for FILE_PATH in "${FILES[@]}"; do
    # Skip if --no-html and FILE_PATH matches *.html
    if [[ "$SKIP_HTML" == true ]] && [[ "$FILE_PATH" == *.html ]]; then
      continue
    fi

    echo "Here's $FILE_PATH:"
    echo ""
    cat "$FILE_PATH"
    echo -e "\n--- End of $FILE_PATH ---\n"
    echo ""
  done

  echo -e "\n--- End of Files ---\n"
} > "$TEMP_FILE"

cat "$TEMP_FILE" | pbcopy
echo "Success: Content of files copied to clipboard."
