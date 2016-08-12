#!/usr/bin/env python

import importlib
import argparse
import os
import sys
try:
    import ujson as json
except ImportError:
    import json

module_name_list = [
        'test',
        ]

parser = argparse.ArgumentParser()
parser.add_argument('-c','-configuration-file',dest='config_file',default=None,help='python file defining "module_name_list"') 
args = parser.parse_args()

if args.config_file is None:
    sys.stderr.write('No configuration file specified; enrichments will be:\n' + str(module_name_list) + '\n')
else:
    # if file not in local directory, temporarily extend path to its location
    config_file_full_path = args.config_file.split('/')
    if len(config_file_full_path) > 1:
        path = '/'.join( config_file_full_path[:-1] )
        sys.path.append( os.path.join(os.getcwd(),path) )
    else:
        sys.path.append(os.getcwd())
    config_module = importlib.import_module( config_file_full_path[-1].rstrip('.py') )  
    sys.path.pop()
    
    if hasattr(config_module,'module_name_list'):
        module_name_list = config_module.module_name_list
    else:
        sys.stderr.write(args.config_file + ' defines no a variable "module_name_list"; using default list.\n')


## fill this list with ordered instances of all enriching classes
full_class_list = []
for module_name in module_name_list:
    ## import by str
    try:
        module = importlib.import_module('gnip_analysis_pipeline.enrichment.' + module_name + '_enrichment')
    except ImportError as e:
        sys.stderr.write('Error importing an enriching module: {}\n{}\n'.format(module_name,str(e))) 
        sys.exit()
    for class_name in module.class_list:
        ## instantiate and add to list
        full_class_list.append(getattr(module,class_name)())

## main loop over tweets
for line in sys.stdin:
    try:
        tweet = json.loads(line)
    except ValueError:
        continue
    # skip Tweets without body
    if 'body' not in tweet:
        continue

    for cls_instance in full_class_list:
        cls_instance.enrich(tweet)
    try:
        sys.stdout.write(json.dumps(tweet) + '\n') 
    except IOError:
        # account for closed output pipe
        break
