#!/bin/bash

var1=$(find ./NGC3227 -mindepth 1 -type f -name "*.fits" -exec printf x \; | wc -c)

var2=$(find ./NGC4235 -mindepth 1 -type f -name "*.fits" -exec printf x \; | wc -c)

var3=$(find ./IRC+10216 -mindepth 1 -type f -name "*.fits" -exec printf x \; | wc -c)

var4=$(find ~/data/auto_tests/all_three -mindepth 1 -type f -name "*.fits" -exec printf x \; | wc -c)

var5=$(($var1+$var2+$var3))

if [ "$var5" -eq "$var4" ]; then
  echo "Number of files matches."
else
  echo "They are not equal"
fi
