#!/usr/bin/env python

import pickle
import argparse
import sys

sys.path.insert(0,"/home/jkolb/Gnip-Trend-Detection")

parser = argparse.ArgumentParser()
parser.add_argument("-i","--input-file",dest="input_file",default=None)
parser.add_argument("-t","--theta",dest="theta",default=float(1))
args = parser.parse_args()

if args.input_file is None:
    sys.stderr.write("Please specify an input file.\n")
    sys.exit(1)
data_summary = pickle.load(open(args.input_file))

global_max_eta = 0
global_max_eta_rule = None
for rule,data in data_summary.items():
    for dt,ct,eta in data:
        if eta > global_max_eta:
            global_max_eta = eta
            global_max_eta_rule = rule
        if eta > args.theta:
            sys.stdout.write("Theta = {0} was exceeded at {1} by measurement: {2}; eta: {3:.1f}\n".format(args.theta,str(dt),rule,eta))
sys.stdout.write("Max eta was {0} for measurement {1:.1f}\n".format(global_max_eta,global_max_eta_rule))
