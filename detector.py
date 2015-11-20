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
            sys.stdout.write("Theta = {} was exceeded at {} by measurement: {}; eta: {}\n".format(args.theta,str(dt),rule,eta))
sys.stdout.write("Max eta was {} for measurement {}\n".format(global_max_eta,global_max_eta_rule))
