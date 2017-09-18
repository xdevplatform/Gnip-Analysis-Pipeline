#!/usr/bin/env python

import importlib
import argparse
import os
import sys
import threading
import multiprocessing as mp
import queue
import time
try:
    import ujson as json
except ImportError:
    import json

QUEUE_SIZE = 1
MAX_WORKERS = 20

parser = argparse.ArgumentParser()
parser.add_argument('-c','-configuration-file',dest='config_file',default=None,help='python file defining "enrichment_class_list"') 
args = parser.parse_args()

prefilters = []

if args.config_file is None:
    sys.stderr.write('No configuration file specified; no enrichments will be run.\n') 
    enrichment_class_list = []
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
    
    if hasattr(config_module,'enrichment_class_list'):
        enrichment_class_list = config_module.enrichment_class_list
    else:
        sys.stderr.write(args.config_file + ' does not define "enrichment_class_list"; no enrichments will be run.\n')

    if hasattr(config_module,'max_workers'):
        MAX_WORKERS = config_module.max_workers

    if hasattr(config_module,'prefilters'):
        prefilters = config_module.prefilters

def worker_func(enrichment_class_list):
    """
    this function runs on new threads/processes
    and reads from a common queue
    """

    class_instance_list = [class_definition() for class_definition in enrichment_class_list]

    while True:
        tweet = in_q.get()

        if tweet is None: # this is the signal to exit
            break
        
        #sys.stderr.write("Got tweet " + tweet['id'] + '\n')
        for cls in class_instance_list:
            enriched_tweet = cls.enrich(tweet)
            #sys.stderr.write("Ran " + cls.__class__.__name__ + " on " + tweet['id'] + '\n')
            if enriched_tweet is not None:
                tweet = enriched_tweet
        #sys.stdout.write(json.dumps(tweet) + '\n')
        
        out_q.put(tweet)
        in_q.task_done()
        

#worker_class = threading.Thread
#in_q = queue.Queue(QUEUE_SIZE)

in_q = mp.JoinableQueue(QUEUE_SIZE)
out_q = mp.Queue()
worker_class = mp.Process

worker_pool = [worker_class(target=worker_func,args=(enrichment_class_list,)) for _ in range(MAX_WORKERS)]   
[worker.start() for worker in worker_pool]

## main loop over tweets
for line in sys.stdin: 
    try:
        tweet = json.loads(line)
    except ValueError:
        continue
    if 'body' not in tweet:
        continue

    if not all([prefilter(tweet) for prefilter in prefilters]):
        continue

    in_q.put(tweet) 

    try:
        enriched_tweet = out_q.get_nowait()  
        sys.stdout.write(json.dumps(enriched_tweet) + '\n')
    except queue.Empty:
        pass


in_q.join()

# kill the workers
for _ in range(len(worker_pool)):
    in_q.put(None)    
                    
for worker in worker_pool:
    worker.join()

while not out_q.empty():
    try:
        enriched_tweet = out_q.get_nowait()  
        sys.stdout.write(json.dumps(enriched_tweet) + '\n')
    except queue.Empty:
        time.sleep(0.1)

