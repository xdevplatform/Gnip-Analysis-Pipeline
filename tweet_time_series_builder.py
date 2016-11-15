#!/usr/bin/env python

import sys
import datetime
import pickle
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

"""
Make counts of things in Tweets, bucketed by a time interval.
"""

logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler() )
logger.setLevel(logging.DEBUG)

# import default measurements list
from gnip_analysis_pipeline.measurement.sample_measurements import measurements_list 
# get the local utilities
from gnip_analysis_pipeline.measurement import utils

# set configuration parameters here. 
config_kwargs = {}
# config_kwargs['top_k'] = 20
# config_kwargs['min_n'] = 10

def aggregate(line_generator,config_kwargs,keep_empty_entries): 
    data = {}

    for item in line_generator:
        try:
            tweet = json.loads(item) 
        except ValueError:
            #sys.stderr.write("BAD TWEET: " + item + '\n')
            continue

        ## throw away Tweets without times (compliance activities)
        if "postedTime" not in tweet:
            continue
        
        ## get time bucket and corresponding data objects
        tweet_time = datetime.datetime.strptime(tweet["postedTime"],twitter_fmt_str)
        time_bucket_key = get_time_bucket(tweet_time)
        
        ## for a new time bucket, we need to initialize the data objects
        if time_bucket_key not in data:
            data[time_bucket_key] = []
            for measurement in measurements_list: 
                data[time_bucket_key].append( measurement(**config_kwargs) ) 
            
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
    args = parser.parse_args()  

    # os module doesn't have yet have cpu_count in py2
    try:
        args.num_cpu = os.cpu_count()
    except AttributeError:
        pass

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
        
        if hasattr(config_module,'measurements_list'):
            measurements_list = config_module.measurements_list
        if hasattr(config_module,'config_kwargs'):
            config_kwargs = config_module.config_kwargs

    twitter_fmt_str = "%Y-%m-%dT%H:%M:%S.000Z"

    if args.bucket_size == "second":
        time_bucket_size_in_sec = 1 
        dt_format = "%Y%m%d%H%M%S"
        def get_time_bucket(tweet_time):
            time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}".format(tweet_time.year
                    ,tweet_time.month
                    ,tweet_time.day
                    ,tweet_time.hour
                    ,tweet_time.minute
                    ,tweet_time.second
                    )
            return time_bucket_key
    elif args.bucket_size == "minute":
        time_bucket_size_in_sec = 60 
        dt_format = "%Y%m%d%H%M"
        def get_time_bucket(tweet_time):
            time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}".format(tweet_time.year
                    ,tweet_time.month
                    ,tweet_time.day
                    ,tweet_time.hour
                    ,tweet_time.minute
                    )
            return time_bucket_key
    elif args.bucket_size == "hour":
        time_bucket_size_in_sec = 3600 
        dt_format = "%Y%m%d%H"
        def get_time_bucket(tweet_time):
            time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}".format(tweet_time.year
                    ,tweet_time.month
                    ,tweet_time.day
                    ,tweet_time.hour
                    )
            return time_bucket_key
    elif args.bucket_size == "day":
        time_bucket_size_in_sec = 3600*24    
        dt_format = "%Y%m%d"
        def get_time_bucket(tweet_time):
            time_bucket_key = "{0:04d}{1:02d}{2:02d}".format(tweet_time.year
                    ,tweet_time.month
                    ,tweet_time.day
                    )
            return time_bucket_key
    elif args.bucket_size == "week":
        dt_format = "%Y%W%w"
        def get_time_bucket(tweet_time):
            # this week number is usually intuitive, but not always;
            # fine for time series analysis
            # https://en.wikipedia.org/wiki/ISO_week_date
            year,week,weekday = tweet_time.isocalendar()
            time_bucket_key = "{:04d}{:02d}0".format(year 
                    ,week
                    ,weekday
                    )
            return time_bucket_key
        ## TODO this isn't correct on the last week of the year
        time_bucket_size_in_sec = 3600*24*7 
    # TODO (need to get correct dt formatting)
    #elif args.bucket_size == "month":
    #    time_bucket_size_in_sec = 3600*24*30     
    #    dt_format = "%Y%m%d"
        #def get_time_bucket(tweet_time):
        #    time_bucket_key = "{0:04d}{1:02d}".format(tweet_time.year
        #            ,tweet_time.month
        #            )
        #    return time_bucket_key
    else:
        # some sort of exception 
        raise ValueError("Bucket size '{}' doesn't make sense".format(args.bucket_size)) 

    if args.input_files is None:
        input_source = fileinput.input(files='-') 
    else:
        input_source = fileinput.input(files=args.input_files,openhook=fileinput.hook_compressed)

    def generate_chunks(iterable, size=10): 
        """ helper function to generated fixed-sized chunks of an iterable """
        iterator = iter(iterable)
        for first in iterator:
            yield itertools.chain([first], itertools.islice(iterator, size - 1))

    pool = multiprocessing.Pool(processes=args.num_cpu)

    # process the chunks of tweets
    # think of this as a mapping step
    results = []
    for chunk_idx,chunk_o_tweets in enumerate(generate_chunks(input_source,args.max_tweets)): 
        logger.debug("Submitting chunk " + str(chunk_idx))
        results.append( pool.apply_async(aggregate,(list(chunk_o_tweets),config_kwargs,args.keep_empty_entries) ) )
    data = []
    while len(results) > 0:
        for result in results:
            if result.ready():
                data.append(result.get())
                results.remove(result)
                break
        time.sleep(0.1)
        if datetime.datetime.now().second%10 == 0:
            time.sleep(1)
            logger.debug(str(len(results)) + ' chunks remaining')


    # combine the measurements
    # think of this as a reducing step
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
                        

    # output the data in CSV
    output_list = []
    for time_bucket_key,measurements in reduced_data.items():
        # the format of this string must be parsable by dateutil.parser.parse
        time_bucket_start = datetime.datetime.strptime(time_bucket_key,dt_format).strftime('%Y%m%d%H%M%S')
        for measurement in measurements:
            for count,counter_name in measurement.get():
                counter_name = utils.sanitize_string(counter_name)
                csv_string = u'{0:d},{1},{2},{3:s}'.format(int(time_bucket_start),
                        time_bucket_size_in_sec,
                        # note: trend input reader splits on ','
                        # choice of '-' is arbitrary!
                        count,
                        counter_name
                        )
                output_list.append(csv_string)

    output_str = '\n'.join(sorted(output_list))
    output_str += '\n'
    if sys.version_info[0] < 3:
        output_str = output_str.encode('utf8')
    sys.stdout.write(output_str)
