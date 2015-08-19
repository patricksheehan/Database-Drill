#!/bin/bash
# moves text files current directory to $1
find . -name "*.txt" -maxdepth 1 -exec sh -c 'mv "$@" "$0"' $1 {} +