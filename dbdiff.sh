#! /bin/bash

set -e

CURR='knowledge.db'
PREV=$(mktemp)

git show HEAD:"$CURR" > "$PREV"

sqldiff "$PREV" "$CURR"
