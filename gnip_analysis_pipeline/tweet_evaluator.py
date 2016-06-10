#!/usr/bin/env python

import argparse
import logging
try:
    import ujson as json 
except ImportError:
    import json
import sys
import datetime
import os

from gnip_analysis_pipeline.evaluation import analysis,output

logger = logging.getLogger('audience_api')
logger.setLevel(logging.WARNING)
logger.addHandler(logging.StreamHandler())

##
## analysis function
##

def run_analysis(input_generator, results): 
    """ iterate over Tweets and analyze"""

    for line in input_generator: 
        # if it's not JSON, skip it
        try:
            tweet = json.loads(line)  
        except ValueError:
            continue
        # analyze each Tweet
        analysis.analyze_tweet(tweet,results)
        
    if "audience_api" in results:
        analysis.analyze_user_ids(results["tweets_per_user"].keys(),results)
    
    return results["tweets_per_user"].keys()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--identifier",dest="unique_identifier", default='0',type=str,
            help="a unique name to identify the conversation/audience")
    parser.add_argument("-c","--do-conversation-analysis",dest="do_conversation_analysis",action="store_true",default=False,
            help="do conversation analysis on Tweets")
    parser.add_argument("-a","--do-audience-analysis",dest="do_audience_analysis",action="store_true",default=False,
            help="do audience analysis on users") 
    parser.add_argument("-i","--input-file-name",dest="input_file_name",default=None,
            help="file containing tweets, tweet IDs, or user IDs; take input from stdin if not present") 
    parser.add_argument('-o','--output-dir',dest='output_directory',default=os.environ['HOME'] + '/tweet_evaluation/',
            help='directory for output files; default is %(default)s')
    args = parser.parse_args()

    # get the time right now, to use in output naming
    time_now = datetime.datetime.now()
    time_string = time_now.isoformat().split(".")[0].translate(None,":") 
    output_directory = '{0}/{1:04d}/{2:02d}/{3:02d}/'.format(args.output_directory.rstrip('/')
            ,time_now.year
            ,time_now.month
            ,time_now.day
            )
   
    # create the output directory if it doesn't exist
    ### 

    results = analysis.setup_analysis(conversation = args.do_conversation_analysis, audience = args.do_audience_analysis) 

    # manage input source
    if args.input_file_name is not None:
        input_generator = open(args.input_file_name)
    else:
        input_generator = sys.stdin

    # run analysis
    run_analysis(input_generator, results)

    # dump the output
    output.dump_results(results, output_directory, args.unique_identifier)
