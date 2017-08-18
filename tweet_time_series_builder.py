#!/usr/bin/env python

import sys
import datetime
import argparse
import importlib
import os
import multiprocessing
import itertools
import time
import logging
import fileinput

try:
    import ujson as json 
except ImportError:
    import json

TWITTER_DT_FORMAT_STR = "%Y-%m-%dT%H:%M:%S.000Z"

"""
Make counts of things in Tweets, bucketed by a time interval.
"""

logger = logging.getLogger(__name__)
handler = logging.StreamHandler() 
handler.setFormatter( logging.Formatter('%(asctime)s %(module)s:%(lineno)s - %(levelname)s - %(message)s') )
handler.setLevel(logging.INFO)
logger.addHandler( handler )
logger.setLevel(logging.INFO)

def aggregate_file(file_name,
        TWITTER_DT_FORMAT_STR,
        dt_bucket_format,
        config_kwargs,
        measurement_class_list,
        keep_empty_entries):
    """
    Aggregator acting on a file name
    File is decompressed and an iterator is passed to 'aggregate'
    """
    decompressed_file_object = fileinput.input(files=file_name,openhook=fileinput.hook_compressed)
    return aggregate(decompressed_file_object,
            TWITTER_DT_FORMAT_STR,
            dt_bucket_format,
            config_kwargs,
            measurement_class_list,
            keep_empty_entries) 

def aggregate(line_generator,
        TWITTER_DT_FORMAT_STR,
        dt_bucket_format,
        config_kwargs,
        measurement_class_list,
        keep_empty_entries):  
    """
    Aggregator acting on an interable
    """
    data = {}

    for tweet_str in line_generator:
        try:
            tweet = json.loads(tweet_str)  
        except ValueError:
            continue

        ## throw away Tweets without times (compliance activities)
        if "postedTime" not in tweet:
            continue
        
        time_bucket_key = datetime.datetime.strptime(tweet["postedTime"],
                TWITTER_DT_FORMAT_STR).strftime(dt_bucket_format)
        
        ## for a new time bucket, we need to initialize the data objects
        if time_bucket_key not in data:
            data[time_bucket_key] = []
            config_kwargs["_datekey"] = time_bucket_key
            for measurement in measurement_class_list:
                # measurement class instances are all constructed with kw args
                data[time_bucket_key].append( measurement(**config_kwargs) ) 
        
        ## get the measurement instances for this bucket
        data_bucket = data[time_bucket_key] 

        ## update all the measurements 
        for measurement in data_bucket:
            measurement.add_tweet(tweet)

    if not keep_empty_entries:
        for dt_key,instance_list in data.items():
            for instance in instance_list:
                if instance.get() == 0:
                    data[dt_key].remove(instance)
    
    return data
    
def combine(data):
    """ 
    Combine measurements across items in 'data'

    'data' is list of results objects calculated 
    for different input files. Each results object is a dict
    of (date_time_bucket, measurement_instance_list) pairs.
    """
    reduced_data = {}
    for chunk_data in data:
        for time_bucket_key,measurements in chunk_data.items():
            for measurement in measurements:
                if time_bucket_key not in reduced_data:
                    reduced_data[time_bucket_key] = [measurement]
                else:
                    measurement_exists = False
                    for existing_measurement in reduced_data[time_bucket_key]:
                        if measurement.get_name() == existing_measurement.get_name():
                            existing_measurement.combine(measurement)
                            measurement_exists = True
                    # add measurement if not found in reduced data for this time bucket
                    if measurement_exists is False:
                        reduced_data[time_bucket_key].append(measurement)
    return reduced_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Produce time series data from Tweet records")

    parser.add_argument('-i','--input-files',dest='input_files',nargs="+",
            default=None,help="input files; if unspecified, stdin is used")
    parser.add_argument('-b','--bucket-size',dest='bucket_size',
            default="day",help="bucket size: second,minute,hour,day; default is %(default)s")
    parser.add_argument('-e','--keep-empty-entries',dest='keep_empty_entries',
            action="store_true",default=False,help="print empty instances; default is %(default)s") 
    parser.add_argument('-c','--config-file',dest='config_file',
            default=None,help='file with local definitions of measurement classes and config')
    parser.add_argument('-m','--max-tweets',dest='max_tweets',type=int,
            default=1000000,help="max number of tweets per aggregator process")
    parser.add_argument('-p','--num-cpu',dest='num_cpu',type=int,
            default=1,help="number of parallel aggregator process")
    parser.add_argument('-v','--verbose',dest='verbose',action='store_true',
            default=False,help="produce verbose output; default is %(default)s")
    args = parser.parse_args()  

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)

    # default measurements list
    measurement_class_list = []

    # default configuration parameters 
    config_kwargs = {}

    if args.config_file is not None:  
        # if config file not in local directory, temporarily extend path to its location
        config_file_full_path = args.config_file.split('/')
        if len(config_file_full_path) > 1:
            path = '/'.join( config_file_full_path[:-1] )
            sys.path.append( os.path.join(os.getcwd(),path) )
        else:
            sys.path.append(os.getcwd())
        config_module = importlib.import_module( config_file_full_path[-1].rstrip('.py') )  
        sys.path.pop()
        
        if hasattr(config_module,'measurement_class_list'):
            measurement_class_list = config_module.measurement_class_list
        else:
            logger.error(args.config_file + ' does not define "measurement_class_list"; no measurements will be run.\n    ')
        if hasattr(config_module,'config_kwargs'):
            config_kwargs = config_module.config_kwargs
    else: 
        logger.info('No configuration file specified; no measurements will be run.\n')


    if args.bucket_size == "second":
        time_bucket_size_in_sec = 1 
        dt_bucket_format = "%Y%m%d%H%M%S"
    elif args.bucket_size == "minute":
        time_bucket_size_in_sec = 60 
        dt_bucket_format = "%Y%m%d%H%M"
    elif args.bucket_size == "hour":
        time_bucket_size_in_sec = 3600 
        dt_bucket_format = "%Y%m%d%H"
    elif args.bucket_size == "day":
        time_bucket_size_in_sec = 3600*24    
        dt_bucket_format = "%Y%m%d"
    else:
        raise ValueError("Time bucket size '{}' is not implemented".format(args.bucket_size)) 

    ## process the Tweets 
    data = []
    if args.input_files is None: 
        # we're reading from stdin and running a single-process
        data.append( aggregate(sys.stdin,
            TWITTER_DT_FORMAT_STR,
            dt_bucket_format,
            config_kwargs,
            measurement_class_list,
            args.keep_empty_entries) )
    else:
        # we will process each input file in a separate process
        mapping_results = []
        pool = multiprocessing.Pool(processes=args.num_cpu)
        for chunk_idx, file_name in enumerate(args.input_files): 
            logger.debug("Submitting chunk " + str(chunk_idx))
            mapping_results.append( pool.apply_async(aggregate_file,(file_name,
                TWITTER_DT_FORMAT_STR,
                dt_bucket_format,
                config_kwargs,
                measurement_class_list,
                args.keep_empty_entries) ) ) 

        # collect results as they finish
        while len(mapping_results) > 0:
            for result in mapping_results:
                if result.ready():
                    data.append(result.get())
                    mapping_results.remove(result)
                    break
            time.sleep(0.1)
            if datetime.datetime.now().second%10 == 0:
                time.sleep(1)
                logger.debug(str(len(mapping_results)) + ' chunks remaining')

    ## combine the measurements
    combined_data = combine(data)

    ## output the data in CSV
    output_list = []
    for time_bucket_key,measurements in combined_data.items():
        # the format of this string must be parsable by dateutil.parser.parse
        time_bucket_start = datetime.datetime.strptime(time_bucket_key,dt_bucket_format).strftime('%Y%m%d%H%M%S')
        for measurement in measurements:
            for count,counter_name in measurement.get():
                csv_string = u'{0:d},{1},{2},{3:s}'.format(int(time_bucket_start),
                        time_bucket_size_in_sec,
                        count,
                        counter_name
                        )
                output_list.append(csv_string)

    output_str = '\n'.join(sorted(output_list))
    output_str += '\n'
    if sys.version_info[0] < 3:
        output_str = output_str.encode('utf8')
    try:
        sys.stdout.write(output_str) 
    except IOError:
        pass
