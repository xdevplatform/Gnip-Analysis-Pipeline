#!/usr/bin/env python

import json
import sys
import pickle
import operator
import ConfigParser
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i","--input-files",dest="input_file_list",default=["data/data.pkl"],nargs="+")
parser.add_argument("-o","--output-file",dest="output_file",default="data/time_series.csv")
parser.add_argument("-c","--config-file",dest="config_file",default=None)
parser.add_argument("-r","--rules-output-file",dest="rules_output",default="rules.json")
parser.add_argument("-b","--bucket-unit",dest="bucket_unit",default="hour")
parser.add_argument("-n","--normalization",dest="norm_file_name",default=None,help="file format: [YYYYmmdd],[VOLUME]")
args = parser.parse_args()

if args.bucket_unit == "day":
    bucket_size_in_sec = 3600*24
    dt_format="%Y%m%d"
else:
    bucket_size_in_sec = 3600
    dt_format="%Y%m%d%H"

data = {}
for f in args.input_file_list:
    try:
        data.update(pickle.load(open(f)))
    except (IOError,EOFError):
        pass
output = open(args.output_file,"w")

## determine output datetime format from GTD config file
if args.config_file is not None:
    cp = ConfigParser.ConfigParser()
    cp.read(args.config_file)
    output_format_str = cp.get("rebin","input_dt_format")
else:
    output_format_str = "%Y%m%d%H%M%S"

## auxilliary task: build rules.json for use with GTD
rules = set()

norm_factors = {}
if args.norm_file_name is not None:
    with open(args.norm_file_name) as f:
        for line in f:
            norm_factors[line.split(",")[0]] = line.split(",")[1]

output_list = []
for time_bucket,time_bucket_data in data.items():
    time_bucket_start = datetime.datetime.strptime(time_bucket,dt_format).strftime(output_format_str)
    for m in time_bucket_data:
        rules.add(m.get_name())
        result = m.get()
        if isinstance(result,int) or isinstance(result,float):
            value = m.get()
            if args.norm_file_name is not None:
                value = value/float(norm_factors[time_bucket[0:8]])
            measurement_str = "{},{},{},{},{}".format(time_bucket_start,m.get_name(),value,-1,bucket_size_in_sec)
            output_list.append(measurement_str)

output_str = '\n'.join(sorted(output_list))
output.write(output_str + '\n')

#i# build and dump rules file
rules_dict = {}
rules_dict["rules"] = [{"value":rule} for rule in rules]
json.dump(rules_dict,open(args.rules_output,"w"))
