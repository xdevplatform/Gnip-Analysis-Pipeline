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
from gnip_analysis_pipeline.measurements import measurements_list

# set configuration parameters here. 
config_kwargs = {}
# config_kwargs['top_k'] = 20
# config_kwargs['min_n'] = 10

parser = argparse.ArgumentParser()
parser.add_argument('-b','--bucket-size',dest='bucket_size',
        default="day",help="bucket size: second,minute,hour,day")
parser.add_argument('-e','--keep-empty-entries',dest='keep_empty_entries',
        action="store_true",default=False,help="print empty instances; default is %(default)s") 
parser.add_argument('-c','--config-file',dest='config_file',
        default=None,help='file with local definitions of measurement classes and config')
args = parser.parse_args() 

if args.config_file is not None:  
    sys.path.append(os.getcwd())
    local_config = importlib.import_module( args.config_file.rstrip('.py') ) 
    if hasattr(local_config,'measurements_list'):
        measurements_list = local_config.measurements_list
    if hasattr(local_config,'config_kwargs'):
        config_kwargs = local_config.config_kwargs

fmt_str = "%Y-%m-%dT%H:%M:%S.000Z"

def get_second_time_bucket(tweet_time):
    time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}".format(tweet_time.year
            ,tweet_time.month
            ,tweet_time.day
            ,tweet_time.hour
            ,tweet_time.minute
            ,tweet_time.second
            )
    return time_bucket_key
def get_minute_time_bucket(tweet_time):
    time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}".format(tweet_time.year
            ,tweet_time.month
            ,tweet_time.day
            ,tweet_time.hour
            ,tweet_time.minute
            )
    return time_bucket_key
def get_hour_time_bucket(tweet_time):
    time_bucket_key = "{0:04d}{1:02d}{2:02d}{3:02d}".format(tweet_time.year
            ,tweet_time.month
            ,tweet_time.day
            ,tweet_time.hour
            )
    return time_bucket_key
def get_day_time_bucket(tweet_time):
    time_bucket_key = "{0:04d}{1:02d}{2:02d}".format(tweet_time.year
            ,tweet_time.month
            ,tweet_time.day
            )
    return time_bucket_key
# TODO (need to get correct dt formatting)
#def get_week_time_bucket(tweet_time):
#    time_bucket_key = "{0:04d}{1:02d}".format(tweet_time.year
#            # this week number is usually intuitive, but not always;
#            # fine for time series analysis
#            # https://en.wikipedia.org/wiki/ISO_week_date
#            ,tweet_time.isocalendar()[1]
#            )
#    return time_bucket_key
#
#def get_month_time_bucket(tweet_time):
#    time_bucket_key = "{0:04d}{1:02d}".format(tweet_time.year
#            ,tweet_time.month
#            )
#    return time_bucket_key

get_time_bucket = locals()["get_"+args.bucket_size +"_time_bucket"]

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
    tweet_time = datetime.datetime.strptime(tweet["postedTime"],fmt_str)
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
    for measurement in measurements_list:
        empty_instance = measurement()
        for key,instance_list in data.items():
            for instance in instance_list:
                if instance.get() == 0:
                    data[key].remove(instance)

# output

if args.bucket_size == "second":
    time_bucket_size_in_sec = 1 
    dt_format = "%Y%m%d%H%M%S"
elif args.bucket_size == "minute":
    time_bucket_size_in_sec = 60 
    dt_format = "%Y%m%d%H%M"
elif args.bucket_size == "hour":
    time_bucket_size_in_sec = 3600 
    dt_format = "%Y%m%d%H"
elif args.bucket_size == "day":
    time_bucket_size_in_sec = 3600*24    
    dt_format = "%Y%m%d"
#elif args.bucket_size == "week":
#    time_bucket_size_in_sec = 3600*24*7 
#    dt_format = "%Y"
#elif args.bucket_size == "month":
#    time_bucket_size_in_sec = 3600*24*30     
#    dt_format = "%Y%m%d"
else:
    # some sort of exception 
    raise Exception("Bucket size doesn't make sense") 

output_list = []
for time_bucket_key,measurements in data.items():
    # the format of this string must be parsable by dateutil.parser.parse
    time_bucket_start = datetime.datetime.strptime(time_bucket_key,dt_format).strftime('%Y%m%d%H%M%S')
    for measurement in measurements:
        for count,counter_name in measurement.get():
            counter_name = unicode(counter_name.replace(',','-'))
            csv_string = u'{0:d},{1},{2},{3:s}'.format(int(time_bucket_start),
                    time_bucket_size_in_sec,
                    # note: trend input reader splits on ','
                    # choice of '-' is arbitrary!
                    count,
                    counter_name
                    )
            output_list.append(csv_string)

output_str = '\n'.join(sorted(output_list))
sys.stdout.write(output_str.encode('utf8') + '\n')
