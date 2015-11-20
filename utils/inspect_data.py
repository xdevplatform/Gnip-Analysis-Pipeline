#!/usr/bin/env python

import pickle as pkl
import argparse
import sys
import os
sys.path.insert(0,os.getcwd())
import measurements


parser = argparse.ArgumentParser()
parser.add_argument('-i','--input-files',dest="input_files",nargs='+')
parser.add_argument('-d','--datetime-bucket',dest="dt_bucket",default=None,help="date-time bucket in YYYYMMDDhh; default is all")
parser.add_argument('-m','--measurement-name',dest="measurement_name",default=None)
args = parser.parse_args()

data = {}
for f in args.input_files:
    try:
        data.update(pkl.load(open(f)))
    except IOError:
        pass

try:
    meas = data[args.dt_bucket]
except KeyError:
    dts = ""
    for dt in data.keys():
        dts += str(dt)
        dts += '\n'
    sys.stderr.write("ERROR: bucket {} was not found in data; options are:\n{}".format(
        args.dt_bucket,
        dts
        ))
    sys.exit(1)

for m in meas:
    if m.__class__.__name__ == args.measurement_name or args.measurement_name is None:
        print( m.get_name() + " : " + str(m.get()))
