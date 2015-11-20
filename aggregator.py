#!/usr/bin/env python

import sys
import ujson as json
import datetime
import pickle
import argparse

from measurements import m as imported_measurements

"""
Make measurements on Tweets, bucketed by a time interval.
"""

parser = argparse.ArgumentParser()
parser.add_argument('-b','--bucket-size',dest='bucket_size',default="day",help="bucket size: hour, day, etc.")
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
def get_month_time_bucket(tweet_time):
    time_bucket_key = "{0:04d}{1:02d}{2:02d}".format(tweet_time.year
            ,tweet_time.month
            )
    return time_bucket_key

get_time_bucket = locals()["get_"+args.bucket_size +"_time_bucket"]

measurements = []
measurements.extend(imported_measurements)

data = {}

for item in sys.stdin:
    tweet = json.loads(item)

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


def same(obj1,obj2):
    """ helper function to identify empty measurement instances """
    if obj1.__class__ != obj2.__class__:
        return False
    if obj1.get() != obj2.get():
        return False
    return True 

if not args.keep_empty_entries:
    for meas in measurements:
        empty_instance = meas()
        for key,instance_list in data.items():
            for instance in instance_list:
                if same(empty_instance,instance):
                    data[key].remove(instance)

sys.stdout.write(pickle.dumps(data))

