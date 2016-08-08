#!/usr/bin/env python

import sys
import os
import datetime
import argparse

from gnip_tweet_evaluation import analysis,output 

parser = argparse.ArgumentParser()
parser.add_argument('-i','--input-file-name',dest='input_file_name',default=None)
parser.add_argument('-n','--unique-identifier',dest='unique_identifier',default="0",
        help='unique identifier to be applied to output file names; default is %(default)s')
parser.add_argument('-o','--output-dir',dest='output_directory',default=os.environ['HOME'] + '/tweet_evaluation/',
        help='directory for output files; default is %(default)s')
args = parser.parse_args()

# set up inputs
if args.input_file_name is not None:
    user_ids = open(args.input_file_name)
else:
    user_ids = sys.stdin
results = {"audience_api":""}
baseline_user_ids = None
groupings = None

# get the time right now, to use in output naming
time_now = datetime.datetime.now()
time_string = time_now.isoformat().split(".")[0].translate(None,":") 
output_directory = '{0}/{1:04d}/{2:02d}/{3:02d}/'.format(args.output_directory.rstrip('/')
        ,time_now.year
        ,time_now.month
        ,time_now.day
        )

# analyze and output
analysis.analyze_user_ids(user_ids, results, groupings, baseline_user_ids)
output.dump_results(results, output_directory, args.unique_identifier)
