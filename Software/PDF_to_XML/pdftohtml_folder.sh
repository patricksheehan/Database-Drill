#!/bin/bash

# Convert PDF files in the current folder to separate XML files also in the current folder
find . -name '*.pdf' -print0 | xargs -0 -n1 pdftohtml -xml -i -q --