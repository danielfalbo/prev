#!/bin/bash

FILES=("README" "prev.py" "edit.sh" "ai.sh" "vercel.json")

TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

{
  for FILE_PATH in "${FILES[@]}"; do
    echo "$FILE_PATH:"
    cat "$FILE_PATH"
    echo -e "\n--- End of $FILE_PATH ---\n"
  done

  echo "Database schema:"
  sqlite3 knowledge.db '.schema'
  echo -e "\n--- End of DB schema ---\n"
} > "$TEMP_FILE"

cat "$TEMP_FILE" | pbcopy
echo "Success: Content of files copied to clipboard."
