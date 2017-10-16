#!/usr/bin/env python

import importlib
import argparse
import os
import sys
import threading
import queue
import time
try:
    import ujson as json
except ImportError:
    import json

def thread_worker_func(enrichment_class,enrichment_idx,thread_idx):
    """
    This function runs on a new thread, gets from an input queue,
    enriches tweets with one enrichment, and puts to an output queue. 

    Parameters
    ----------
    enrichment_class : class definition object
    enrichment_idx : int 
        Index of enrichment in enrichment list
    thread_idx : int
        Index of thread for this enrichment
    """

    enrichment_class_instance = enrichment_class()
    input_q = queue_pool[enrichment_idx]
    output_q = queue_pool[enrichment_idx+1]

    while True:
        tweet = input_q.get()

        if tweet is None: # this is the signal to exit
            input_q.task_done()
            break
        
        enriched_tweet = enrichment_class_instance.enrich(tweet)
        if enriched_tweet is not None:
            tweet = enriched_tweet
        
        output_q.put(tweet)
        input_q.task_done()
    
def output_worker_func():
    """
    Serializes enriched Tweet objects; runs on a dedicated thread
    """

    input_q = queue_pool[-1]

    while True:

        tweet = input_q.get()
        if tweet is None: # this is the signal to exit
            break
        
        out_str = json.dumps(tweet) + '\n' 
        try:
            sys.stdout.write(out_str) 
        except BrokenPipeError: # check for closed output pipe
            break


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-c','-configuration-file',dest='config_file',default=None,help='python file defining "enrichment_class_list"') 
    args = parser.parse_args()

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

    input_q = queue.Queue(2)
    queue_pool = [input_q] # input queue is the first element of queue_pool
    thread_pool_list = []

    # create and start all enrichment threads
    for enrichment_idx,(enrichment_class,n_threads) in enumerate(enrichment_class_list):
        queue_pool.append(queue.Queue(n_threads*2 + 1))
        thread_pool = [threading.Thread(target=thread_worker_func,
            args=(enrichment_class,enrichment_idx,i_thread)) 
            for i_thread in range(n_threads)] 
        [thread.start() for thread in thread_pool]
        thread_pool_list.append(thread_pool)

    # create and start output thread
    output_thread = threading.Thread(target=output_worker_func)
    output_thread.start()

    ## main loop over tweets
    for line in sys.stdin: 
        try:
            tweet = json.loads(line)
        except ValueError:
            continue
        if 'body' not in tweet:
            continue

        input_q.put(tweet) 


    # send the "all done" signals to flush the queues 
    # and join the queues and threads
    
    for enrichment_idx,(enrichment_class,n_threads) in enumerate(enrichment_class_list):
        # cause the worker functions on each thread to exit
        for i in range(n_threads):
            queue_pool[enrichment_idx].put(None)
        # join this enrichment's input queue
        queue_pool[enrichment_idx].join()
        # join this enrichment's threads
        [thread.join() for thread in thread_pool_list[enrichment_idx]]
    
    queue_pool[-1].put(None)
    output_thread.join()
   
