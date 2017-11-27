#!/usr/bin/env python

import importlib
import argparse
import os
import sys
import threading
import queue
import time
import logging
import multiprocessing as mp
try:
    import ujson as json
except ImportError:
    import json

logging.basicConfig(level=logging.WARN, 
        format='%(asctime)s %(module)s:%(lineno)s - %(levelname)s - %(message)s'
        )

def worker_func(enrichment_class,enrichment_idx,worker_idx):
    """
    This function runs on a new worker, gets from an input queue,
    enriches tweets with one enrichment, and puts to an output queue. 

    Parameters
    ----------
    enrichment_class : class definition object
    enrichment_idx : int 
        Index of enrichment in enrichment list
    worker_idx : int
        Index of worker for this enrichment
    """

    enrichment_class_instance = enrichment_class()
    input_q = queue_pool[enrichment_idx]
    output_q = queue_pool[enrichment_idx+1]

    logging.info(f"Entered worker {worker_idx}") 
    while True:
        try:
            tweet = input_q.get() 
        except TypeError:
            input_q.task_done()
            continue

        if tweet is None: # this is the signal to exit
            logging.info(f"Worker {worker_idx} got None") 
            input_q.task_done()
            break
        logging.debug(f"Worker {worker_idx} got tweet {tweet['id']}")
        
        enriched_tweet = enrichment_class_instance.enrich(tweet)
        if enriched_tweet is not None:
            tweet = enriched_tweet
        
        output_q.put(tweet)
        input_q.task_done()
    logging.info(f"Exiting worker {worker_idx}")
    
def output_func():
    """
    Serializes enriched Tweet objects; runs on a dedicated worker
    """

    input_q = queue_pool[-1]
    logging.info("entered output worker") 
    counter = 0

    while True:

        tweet = input_q.get()
        if tweet is None: # this is the signal to exit
            logging.info(f"Output worker got None") 
            input_q.task_done()
            break

        counter += 1
        if args.verbose and counter%1000==0:
            logging.warn(f"{counter} tweets enriched\n")
        
        out_str = json.dumps(tweet) + '\n' 
        try:
            sys.stdout.write(out_str) 
        except BrokenPipeError: # check for closed output pipe
            break
    logging.info(f"Exiting output worker")

def cleanup_concurrent_operation():
    """
    Flush the queues and join the queues and workers  
    The "all done" signal is None
    """
    
    for enrichment_idx,(enrichment_class,n_workers) in enumerate(enrichment_class_list):
        # cause the worker functions on each worker to exit
        for i in range(n_workers):
            queue_pool[enrichment_idx].put(None)
        # join this enrichment's input queue
        queue_pool[enrichment_idx].join()
        # join this enrichment's workers
        [worker.join() for worker in worker_pool_list[enrichment_idx]]
    
    queue_pool[-1].put(None)
    output_worker.join()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--configuration-file',dest='config_file',default=None,
            help='python file defining "enrichment_class_list"') 
    parser.add_argument('-s','--simple-version',dest='do_simple_architecture',action='store_true',default=False,
            help='use simple, non-concurrent architecture') 
    parser.add_argument('-p','--use-processes',dest='use_processes',action='store_true',default=False,
            help='use processes instread of threads') 
    parser.add_argument('-v','--display-counter',dest='verbose',action='store_true',default=False,
            help='display counter of enriched tweets') 
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
   
    if args.do_simple_architecture: 
        # create instances of all configured classes
        class_instance_list = [class_definition() for class_definition,_ in enrichment_class_list]
    else: # use concurrent architecture
        if args.use_processes:
            queue_type = mp.JoinableQueue
            worker_type = mp.Process
        else:
            queue_type = queue.Queue
            worker_type = threading.Thread

        # set up workers and queues
        input_q = queue_type(10)
        queue_pool = [input_q] # input queue is the first element of queue_pool
        worker_pool_list = []

        # create and start all enrichment workers
        for enrichment_idx,(enrichment_class,n_workers) in enumerate(enrichment_class_list):
            logging.info("Starting {} workers for enrichment {}".format(n_workers,enrichment_class.__name__))
            queue_pool.append(queue_type(n_workers*2 + 1))
            worker_pool = [worker_type(target=worker_func,
                args=(enrichment_class,enrichment_idx,worker_idx)) 
                for worker_idx in range(n_workers)] 
            [worker.start() for worker in worker_pool]
            worker_pool_list.append(worker_pool)

        # create and start output worker
        output_worker = worker_type(target=output_func)
        output_worker.start()

    ## main loop over tweets
    for line in sys.stdin: 
        try:
            tweet = json.loads(line)
        except ValueError:
            continue
        if 'body' not in tweet:
            continue

        if args.do_simple_architecture:
            for cls_instance in class_instance_list:
                tweet = cls_instance.enrich(tweet)
            try:
                sys.stdout.write(json.dumps(tweet) + '\n') 
            except IOError:
                # account for closed output pipe
                break
        else:
            input_q.put(tweet) 

    if not args.do_simple_architecture:
        cleanup_concurrent_operation()
   
