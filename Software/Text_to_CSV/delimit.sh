#!/bin/bash

# Delete commas in text files
LANG=C && LC_ALL=C find . -name "*.txt" | xargs sed -i '' 's/,//g'
# Delete ' marks
LANG=C && LC_ALL=C find . -name "*.txt" | xargs sed -i '' "s/'//g"
# Replace large white spaces with commas
LANG=C && LC_ALL=C find . -name "*.txt" | xargs sed -i '' 's/ \{2,200\}/,/g'
# Delete empty lines
LANG=C && LC_ALL=C find . -name "*.txt" | xargs sed -i '' '/^$/d'