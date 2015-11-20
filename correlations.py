#!/usr/bin/env python 

import collections
import itertools
import sys
import operator
import argparse

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("-i","--input-file",dest="input_file_names",nargs="+",default=None,help="input CSV file(s)")
parser.add_argument("-p","--precision",dest="precision",default=5,help="correlation coefficient precision")
args = parser.parse_args()

measurements = collections.defaultdict(list)
for input_file_name in args.input_file_names:
    with open(input_file_name) as f:
        sys.stdout.write("Opening {}\n".format(input_file_name))
        for line in f:
            dt,measurement,count,total_count,tb_size_in_sec = line.split(',')
            measurements[measurement].append(int(count))

results = []
for pair in itertools.combinations(measurements.keys(),2):
    series_0 = measurements[pair[0]]
    series_1 = measurements[pair[1]]
    r = np.corrcoef(series_0,series_1)[0][1]
    r_round = round(r,args.precision)
    results.append((pair,r_round))

for pair,r in sorted(results,key=operator.itemgetter(1)): 
    sys.stdout.write("{},{},{}\n".format(r,pair[0],pair[1]))
