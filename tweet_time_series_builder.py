#!/usr/bin/env python

import sys
import datetime
import pickle
import argparse
import importlib
import os

try:
    import ujson as json 
except ImportError:
    import json

"""
Make counts of things in Tweets, bucketed by a time interval.
"""

# import default measurements list
from gnip_analysis_pipeline.measurement.sample_measurements import measurements_list 
# get the local utilities
from gnip_analysis_pipeline.measurement import utils

# set configuration parameters here. 
config_kwargs = {}
# config_kwargs['top_k'] = 20
# config_kwargs['min_n'] = 10

parser = argparse.ArgumentParser()
parser.add_argument('-b','--bucket-size',dest='bucket_size',
        default="day",help="bucket size: second,minute,hour,day; default is %(default)s")
parser.add_argument('-e','--keep-empty-entries',dest='keep_empty_entries',
        action="store_true",default=False,help="print empty instances; default is %(default)s") 
parser.add_argument('-c','--config-file',dest='config_file',
        default=None,help='file with local definitions of measurement classes and config')
args = parser.parse_args() 

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


data = {}

for item in sys.stdin:
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


if not args.keep_empty_entries:
    for dt_key,instance_list in data.items():
        for instance in instance_list:
            if instance.get() == 0:
                data[dt_key].remove(instance)

# output


output_list = []
for time_bucket_key,measurements in data.items():
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
if sys.version_info[0] < 3:
    output_str.encode('utf8')
sys.stdout.write(output_str + '\n')
