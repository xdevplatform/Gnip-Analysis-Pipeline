#!/usr/bin/env python

import sys
import ujson as json
import importlib

module_name_list = [
        "test_module"
        ]

## fill this list with ordered instances of all enriching classes
full_class_list = []
for module_name in module_name_list:
    ## import by str
    module = importlib.import_module("enrichments." + module_name)
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
    sys.stdout.write(json.dumps(tweet) + '\n')
