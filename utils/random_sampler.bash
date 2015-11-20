#!/bin/bash

if [[ "$1" == "" ]]; then
    echo ""
    echo "usage: random_sampler.bash FACTOR"
    echo ""
    echo "prints to STDOUT approximately 1/FACTOR of the lines passed to STDIN"
    echo ""
    exit
fi
awk -v SEED=$RANDOM -v FACTOR=$1 'BEGIN{srand(SEED)} {if( rand() < 1/FACTOR) print $0}' <&0 
