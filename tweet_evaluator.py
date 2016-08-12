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
import importlib

from gnip_tweet_evaluation import analysis,output

"""
Perform audience and/or conversation analysis on a set of Tweets.
"""

logger = logging.getLogger('audience_api')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

logger = logging.getLogger('analysis') 
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--identifier",dest="unique_identifier", default='0',type=str,
            help="a unique name to identify the conversation/audience; default is '%(default)s'")
    parser.add_argument("-c","--do-conversation-analysis",dest="do_conversation_analysis",action="store_true",default=False,
            help="do conversation analysis on Tweets")
    parser.add_argument("-a","--do-audience-analysis",dest="do_audience_analysis",action="store_true",default=False,
            help="do audience analysis on users") 
    parser.add_argument("-i","--input-file-name",dest="input_file_name",default=None,
            help="file containing tweet data; take input from stdin if not present") 
    parser.add_argument('-o','--output-dir',dest='output_directory',default=os.environ['HOME'] + '/tweet_evaluation/',
            help='directory for output files; default is %(default)s')
    parser.add_argument('-s','--splitting-config',dest='splitting_config',default=None,
            help='module that contains functions on Tweets that define the "analyzed" and "baseline" sets')
    args = parser.parse_args()

    # get the time right now, to use in output naming
    time_now = datetime.datetime.now()
    time_string = time_now.isoformat().split(".")[0].translate(None,":") 
    output_directory = '{0}/{1:04d}/{2:02d}/{3:02d}/'.format(args.output_directory.rstrip('/')
            ,time_now.year
            ,time_now.month
            ,time_now.day
            )
   
    # configure the results object and manage splitting
    splitting_config = None
    if args.splitting_config is not None:
        # if file not in local directory, temporarily extend path to its location
        config_file_full_path = args.config_file.split('/')
        if len(config_file_full_path) > 1:
            path = '/'.join( config_file_full_path[:-1] )
            sys.path.append( os.path.join(os.getcwd(),path) )
        else:
            sys.path.append(os.getcwd())
        splitting_config = importlib.import_module( config_file_full_path[-1].rstrip('.py') ).splitting_config
        sys.path.pop()
        
        results = analysis.setup_analysis(conversation = args.do_conversation_analysis, 
                audience = args.do_audience_analysis,
                identifier = 'analyzed',
                input_results = {}) 
        results = analysis.setup_analysis(conversation = args.do_conversation_analysis, 
                audience = args.do_audience_analysis,
                identifier = 'baseline',
                input_results = results) 
    else:
        results = analysis.setup_analysis(conversation = args.do_conversation_analysis, audience = args.do_audience_analysis) 

    # manage input sources, file opening, and deserialization
    if args.input_file_name is not None:
        tweet_generator = analysis.deserialize_tweets(open(args.input_file_name))
    else:
        tweet_generator = analysis.deserialize_tweets(sys.stdin)

    # run analysis
    analysis.analyze_tweets(tweet_generator, results, splitting_config)

    # dump the output
    output.dump_results(results, output_directory, args.unique_identifier)
