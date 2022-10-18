#!/bin/bash

# Remove excluded notebooks
for f in $(cat .ci_support/exclude); do 
    rm "notebooks/$f";     
done;

kernel="python3"

# execute notebooks
i=0;
for notebook in $(ls notebooks/*.ipynb); do 
    papermill ${notebook} ${notebook%.*}-out.${notebook##*.} -k $kernel || i=$((i+1));
done;

# push error to next level
if [ $i -gt 0 ]; then
    exit 1;
fi;
