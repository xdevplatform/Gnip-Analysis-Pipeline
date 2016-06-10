#!/usr/bin/env python

import sys
import datetime
import pickle
import argparse

try:
    import ujson as json 
except ImportError:
    import json

from gnip_analysis_pipeline.measurements import m as imported_measurements

"""
Make measurements on Tweets, bucketed by a time interval.
"""

parser = argparse.ArgumentParser()
parser.add_argument('-b','--bucket-size',dest='bucket_size',default="day",help="bucket size: hour, day, week")
parser.add_argument('-e','--keep-empty-entries',dest='keep_empty_entries',action="store_true",default=False,help="print empty instances")
args = parser.parse_args() 

fmt_str = "%Y-%m-%dT%H:%M:%S.000Z"

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
# TODO
#def get_week_time_bucket(tweet_time):

#def get_month_time_bucket(tweet_time):
#    time_bucket_key = "{0:04d}{1:02d}".format(tweet_time.year
#            ,tweet_time.month
#            )
#    return time_bucket_key

get_time_bucket = locals()["get_"+args.bucket_size +"_time_bucket"]

measurements = []
measurements.extend(imported_measurements)

data = {}

for item in sys.stdin:
    try:
        tweet = json.loads(item) 
    except ValueError:
        sys.stderr.write("BAD TWEET: " + item + '\n')
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
        for meas in measurements:
            data[time_bucket_key].append( meas() )
        
    data_bucket = data[time_bucket_key] 

    ## update all the measurements 
    for meas in data_bucket:
        meas.add_tweet(tweet)


if not args.keep_empty_entries:
    for meas in measurements:
        empty_instance = meas()
        for key,instance_list in data.items():
            for instance in instance_list:
                if instance.get() == 0:
                    data[key].remove(instance)

# output

output_format_str = "%Y%m%d%H%M%S"

if args.bucket_size == "hour":
    time_bucket_size_in_sec = 3600 
    dt_format = "%Y%m%d%H"
elif args.bucket_size == "day":
    time_bucket_size_in_sec = 3600*24    
    dt_format = "%Y%m%d"
#elif args.bucket_size == "week":
#    time_bucket_size_in_sec = 3600*24*7 
#    dt_format = "%Y"
else:
    # some sort of exception 
    raise Exception('not really a thing') 

output_list = []
for time_bucket_key,measurements in data.items():
    time_bucket_start = datetime.datetime.strptime(time_bucket_key,dt_format).strftime(output_format_str)
    for meas in measurements:
        csv_string = '{0:d},{1:s},{2},{3},{4}'.format(int(time_bucket_start),
                # note: trend input reader splits on ','
                # choice of '-' is arbitrary!
                meas.get_name().replace(',','-'), 
                meas.get(),
                -1,
                time_bucket_size_in_sec)
        output_list.append(csv_string)

output_str = '\n'.join(sorted(output_list))
sys.stdout.write(output_str + '\n')
