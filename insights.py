#!/usr/bin/env python

import argparse
import ujson as json
import sys
import datetime

from insights import analysis,output,search

parser = argparse.ArgumentParser()
parser.add_argument("-n","--audience_name",dest="audience_identifier", default=None,
        help="must provide a name string for the conversation/audience")
parser.add_argument("-c","--do-conversation-analysis",dest="do_conversation_analysis",action="store_true",default=False,
        help="do conversation analysis on Tweets")
parser.add_argument("-a","--do-audience-analysis",dest="do_audience_analysis",action="store_true",default=False,
        help="do audience analysis on users") 
parser.add_argument("-i","--input-file-name",dest="input_file_name",default=None,
        help="file containing tweets, tweet IDs, or user IDs; take input from stdin if not present")
parser.add_argument("-f","--full-tweet-input",dest="full_tweet_input",action="store_true",default=False,
        help="input is JSON-formatted tweet data")
parser.add_argument("-t","--tweet-id-input",dest="tweet_id_input",action="store_true",default=False,
        help="input is tweet IDs") 
parser.add_argument("-u","--user-id-input",dest="user_id_input",action="store_true",default=False,
        help="input is user IDs") 
args = parser.parse_args()

# sanity checking
if (args.full_tweet_input and args.tweet_id_input) or (args.full_tweet_input and args.user_id_input) or (args.tweet_id_input and args.user_id_input):
    sys.stderr.write("Must not choose more than one input type\n")
    sys.exit()

##
## analysis
##

# set up input
assert args.audience_identifier is not None, "You must provide an id for the analysis"

time_string = datetime.datetime.now().isoformat().split(".")[0].translate(None,":")
conversation_results = {"audience_id_string": args.audience_identifier + "_" + time_string }
audience_results = {"audience_id_string": args.audience_identifier + "_" + time_string}

if args.input_file_name is not None:
    generator = open(args.input_file_name)
else:
    generator = sys.stdin

if args.full_tweet_input:
    user_ids = []
    for line in generator: 
        try:
            tweet = json.loads(line)  
            if "actor" not in tweet:
                continue
            if args.do_conversation_analysis:
                analysis.analyze_tweet(tweet,conversation_results)
            if args.do_audience_analysis:
                user_id = int(tweet["actor"]["id"].split(":")[2])
                if user_id not in user_ids:
                    bio = tweet["actor"]["summary"] 
                    if bio is not None and bio != "":
                        analysis.analyze_bio(tweet,audience_results)
                    user_ids.append( user_id ) 
        except ValueError:
            continue
        
    if args.do_audience_analysis:
        analysis.analyze_user_ids(set(user_ids),audience_results)

if args.tweet_id_input:
    tweet_ids = [tweet_id for tweet_id in generator]  
    tweet_ids = set(tweet_ids)

    user_ids = []
    # this might not scale
    tweets = search.get_tweets_from_ids(tweet_ids)
    for tweet in tweets: 
        if args.do_conversation_analysis:
            analysis.analyze_tweet(tweet,conversation_results)
        
        if args.do_audience_analysis:
            user_id = int(tweet["actor"]["id"].split(":")[2]) 
            if user_id not in user_ids:
                #bio = tweet["actor"]["summary"]
                analysis.analyze_bio(tweet,audience_results)
                user_ids.append( user_id) 
    
    if args.do_audience_analysis:        
        analysis.analyze_user_ids(user_ids,audience_results)

if args.user_id_input:
    user_ids = [user_id for user_id in generator]
    user_ids = set(user_ids)

    if args.do_audience_analysis:
        analysis.analyze_user_ids(user_ids,audience_results)

    # this might not scale
    tweets = search.get_tweets_from_user_ids(user_ids)
    user_ids = []
    for tweet in tweets: 
        if args.do_conversation_analysis:
            analysis.analyze_tweet(tweet,conversation_results)
    
        if args.do_audience_analysis:
            user_id = int(tweet["actor"]["id"].split(":")[2]) 
            if user_id not in user_ids:
                bio = tweet["actor"]["summary"]
                analysis.analyze_bio(bio,audience_results) 
                user_ids.append(user_id)

##
## format and dump results
##
if args.do_conversation_analysis:
    analysis.summarize_tweets(conversation_results)
    output.dump_conversation(conversation_results,args)
if args.do_audience_analysis:
    analysis.summarize_audience(audience_results)
    output.dump_audience(audience_results,args)

