#!/bin/bash

files=(PDFs/*)
for (( i=0; i<50; i++ )); do
    keys=("${!files[@]}")
    rnd=$(( RANDOM % ${#keys[@]} ))
    key=${keys[$rnd]}
    cp "${files[$key]}" "$./PDF_Sample"
    unset files[$key]
done
