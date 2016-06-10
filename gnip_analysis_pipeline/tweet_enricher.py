#!/usr/bin/env python

import importlib
try:
    import ujson as json
except ImportError:
    import json
import sys

module_name_list = [
        "test",
        ]

## fill this list with ordered instances of all enriching classes
full_class_list = []
for module_name in module_name_list:
    ## import by str
    try:
        module = importlib.import_module("gnip_analysis_pipeline.enrichments." + module_name) 
    except ImportError, e:
        sys.stderr.write('Error importing an enriching module: {}\n'.format(module_name)) 
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
        break
