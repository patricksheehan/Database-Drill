#!/bin/bash

# Convert PDF files in the current folder to separate text files also in the current folder
find . -name '*.pdf' -print0 | xargs -0 -n1 pdftotext -table -clip -nopgbrk -fixed 1 --