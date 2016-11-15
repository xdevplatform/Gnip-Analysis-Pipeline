#!/usr/bin/env python

import importlib
import argparse
import os
import sys
try:
    import ujson as json
except ImportError:
    import json

class_list = []

parser = argparse.ArgumentParser()
parser.add_argument('-c','-configuration-file',dest='config_file',default=None,help='python file defining "class_list"') 
args = parser.parse_args()

prefilters = []

if args.config_file is None:
    sys.stderr.write('No configuration file specified; no enrichments will be run.\n') 
else:
    # if config file not in local directory, temporarily extend path to its location
    config_file_full_path = args.config_file.split('/')
    if len(config_file_full_path) > 1:
        path = '/'.join( config_file_full_path[:-1] )
        sys.path.append( os.path.join(os.getcwd(),path) )
    else:
        sys.path.append(os.getcwd())
    config_module = importlib.import_module( config_file_full_path[-1].rstrip('.py') )  
    sys.path.pop()
    
    if hasattr(config_module,'class_list'):
        class_list = config_module.class_list
    else:
        sys.stderr.write(args.config_file + ' does not define "class_list"; no enrichments will be run.\n')

    if hasattr(config_module,'prefilters'):
        prefilters = config_module.prefilters

# create instances of all configured classes
class_instance_list = [class_definition() for class_definition in class_list]

## main loop over tweets
for line in sys.stdin:
    try:
        tweet = json.loads(line)
    except ValueError:
        continue
    # skip Tweets without body
    if 'body' not in tweet:
        continue

    if not all([prefilter(tweet) for prefilter in prefilters]):
        continue

    for cls_instance in class_instance_list:
        cls_instance.enrich(tweet)
    try:
        sys.stdout.write(json.dumps(tweet) + '\n') 
    except IOError:
        # account for closed output pipe
        break
