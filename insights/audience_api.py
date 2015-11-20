#!/usr/bin/env python

import requests 
from requests_oauthlib import OAuth1 
import pprint
import json
from numpy import ceil
import yaml
import os
import argparse
import datetime

def single_audience_query(user_ids, groupings, audience_name,  max_upload_size = 100000, max_segment_size = 3000000, min_audience_size = 10000, log_file_location = None):
    """
    Make 1 request for audience information
    """

    if len(user_ids) < min_audience_size:
        return "Not enough users to run the audience API"

    # Set up credentials (user-specific)
    creds = yaml.load(open("/mnt/home/fiona/.audience_api_creds","r"))
    auth=OAuth1(creds["consumer_key"],creds["consumer_secret"],creds["token"],creds["token_secret"])
    
    base_url = creds["url"]
    json_header = {"Content-Type" : "application/json"}

    if log_file_location is None:
        log_file_loc = "/home/jkolb/DDIS-DSO/ABInBev/dsrp/data/audience_and_convo_insights/"
    else:
        log_file_loc = log_file_location

    try:
        os.stat(log_file_loc + audience_name + "_logging")
    except:
        os.mkdir(log_file_loc + audience_name + "_logging")

    logging = open(log_file_loc + audience_name + "_logging" + "/log_file_for_" + audience_name, "w")

    # split the UIDS into max_upload_size 
    user_id_chunks = chunks(list(set(user_ids)), max_upload_size)
    uids_json_encoded = []
    for uid_chunk in user_id_chunks:
        uids_json_encoded.append(json.dumps({"user_ids": [str(x) for x in uid_chunk]}))

    # create a segment
    segment_response = requests.post(base_url + "/segments"
            , auth = auth
            , headers = json_header
            , data = json.dumps({"name": audience_name + "segment"})
            )
    logging.write(segment_response.text + "\n")
    segment_id = segment_response.json()["id"]

    # upload the chunks to a segment
    for uid_chunk_json_encoded in uids_json_encoded:
        segment_post_ids = requests.post(base_url + "/segments/" + segment_id + "/ids"
                , auth = auth
                , headers = json_header
                , data = uid_chunk_json_encoded
                )
        logging.write(segment_post_ids.text + "\n")

    # add the segment to an audience
    audience_post = requests.post(base_url + "/audiences"
            , auth = auth
            , headers = json_header
            , data = json.dumps({"name": audience_name, "segment_ids": [segment_id]})
            )
    logging.write(audience_post.text + "\n")
    audience_id = audience_post.json()["id"]

    # make a request for information about the audience
    audience_info = requests.post(base_url + "/audiences/" + audience_id + "/query"
            , auth = auth
            , headers = json_header
            , data = groupings
            )
    logging.write(groupings + "\n")
    logging.write(audience_info.text.encode("utf-8"))
    
    return audience_info.json()

def many_audience_query(user_ids, groupings, audience_name, max_upload_size = 100000, max_segment_size = 3000000, max_audience_size = 3000000, min_audience_size = 10000, log_file_location = None):
    """
    Make 1 request for audience information for each max_audience_size audience in the set
    """
    if len(user_ids) < min_audience_size:
        return "Audience is too small to use the Audience API"
    
    api_results = []
    unique_user_ids = list(set(user_ids))
    num_audiences = int(ceil(len(unique_user_ids)/float(max_audience_size)))
    size_audiences = int(ceil(len(unique_user_ids)/float(num_audiences)))
    
    for i, audience_chunk in enumerate(chunks(unique_user_ids, size_audiences)):
        api_results.append(single_audience_query(audience_chunk, groupings, audience_name + "_" + str(i), max_upload_size = 100000, max_segment_size = 3000000, log_file_location = log_file_location))
    return api_results

def existing_audience_query(groupings, audience_name, log_file_location = None):
    
    # Set up credentials (user-specific)
    creds = yaml.load(open("audience_api_creds.yaml","r"))
    auth=OAuth1(creds["consumer_key"],creds["consumer_secret"],creds["token"],creds["token_secret"])
    
    base_url = creds["url"]
    json_header = {"Content-Type" : "application/json"} 
   
    if log_file_location is None:
        log_file_loc = "/home/jkolb/DDIS-DSO/ABInBev/dsrp/data/audience_and_convo_insights/"
    else:
        log_file_loc = log_file_location
    
    try:
        os.stat(log_file_loc + audience_name + "_logging")
    except:
        os.mkdir(log_file_loc + audience_name + "_logging")

    logging = open(log_file_loc + audience_name + "_logging" + "/log_file_for_" + audience_name.split("_")[0], "w")
    
    logging.write(groupings + "\n")
    # make a request for information about the audience
    all_audiences = requests.get(base_url + "/audiences"
            , auth = auth
            )

    audience_id = 0
    for audience in all_audiences.json():
        if audience["name"] == audience_name:
            audience_id = audience["id"]
            break
    if audience_id == 0:
        "That audience doesn't exist"

    else:
        audience_info = requests.post(base_url + "/audiences/" + audience_id + "/query"
                , auth = auth
                , headers = json_header
                , data = groupings
                )
        logging.write(audience_info.text)
    
        return audience_info.json()

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def call_audience_api(user_ids,audience_name, groupings = None,max_audience_size=3000000, log_file_location=None):
    """ call to Audience API goes here """

    aud_name = audience_name
    if groupings is not None:
        use_groupings = groupings
    else:
        grouping_dict = {"groupings": {
            "gender": {"group_by": ["user.gender"]}
            , "location_country": {"group_by": ["user.location.country"]}
            , "location_country_region": {"group_by": ["user.location.country", "user.location.region"]}
            , "location_country_region_metro": {"group_by": ["user.location.country", "user.location.region", "user.location.metro"]}
            , "interest": {"group_by": ["user.interest"]}
            , "tv_genre": {"group_by": ["user.tv.genre"]}
            , "device_os": {"group_by": ["user.device.os"]}
            , "device_network": {"group_by": ["user.device.network"]}
            , "language": {"group_by": ["user.language"]}}}
        use_groupings = json.dumps(grouping_dict)
    
    audience_api_results = many_audience_query(user_ids, use_groupings, aud_name,  
            max_upload_size = 100000, max_segment_size = 3000000, max_audience_size = max_audience_size, min_audience_size = 10000, log_file_location = log_file_location)
    
    return audience_api_results

def audience_insights_csv_1(audience_api_result):
    d = flatten_dict_1(audience_api_result)
    l = d.items()
    return sorted(l, key = lambda x : (x[0].split("|")[0], -1*int(x[-1])))
    #print i[0] + " | " + str(int(i[1]))

def flatten_dict_1(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + ' | ' + k, v) for k, v in flatten_dict_1(value).items() ]
        else:
            return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--audience_name",dest="audience_identifier", default=None,
            help="must provide a name string for the conversation/audience, alphanumeric + underscore only")
    parser.add_argument("-i","--input-file-name",dest="input_file_name",default=None,
            help="file containing tweets, tweet IDs, or user IDs; take input from stdin if not present")
    parser.add_argument("-f","--full-tweet-input",dest="full_tweet_input",action="store_true",default=False,
            help="input is JSON-formatted tweet data")
    parser.add_argument("-u","--user-id-input",dest="user_id_input",action="store_true",default=True,
            help="input is user IDs")
    parser.add_argument("-g","--groupings",dest="groupings_file",default=None,
            help="groupings file, if None default groupings are used")
    parser.add_argument("-d", "--results-detination",dest="results_file",default="",
            help="destination file for the audience api results")
    parser.add_argument("-m","--max_audience_size",dest="max_audience_size",default=300000,type=int,
            help="the maximum audience size")
    args = parser.parse_args()
    
    assert args.audience_identifier is not None, "You must provide an id for the analysis"
    
    time_string = datetime.datetime.now().isoformat().split(".")[0].translate(None,":")
    aud_name =  args.audience_identifier + "_" + time_string 
    
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
                user_id = int(tweet["actor"]["id"].split(":")[2])
                if user_id not in user_ids:
                    user_ids.append( user_id ) 
            except ValueError:
                continue
            
    if args.user_id_input:
        user_ids = [user_id.strip() for user_id in generator]
        user_ids = list(set(user_ids))

    try:
        os.stat(args.results_file + aud_name + "_logging")
    except:
        os.mkdir(args.results_file + aud_name + "_logging")

    try:
        os.stat(args.results_file + aud_name)
    except:
        os.mkdir(args.results_file + aud_name)
    
    if args.groupings_file is not None:
        groupings = json.dumps(json.load(open(args.groupings_file,"r")))
    else: 
        groupings = None
    
    audience_api_results = call_audience_api(user_ids, aud_name, groupings=groupings, max_audience_size = args.max_audience_size, log_file_location = args.results_file + aud_name + "_logging/")

    print "\nAudience API Results"
    if audience_api_results != "Audience is too small to use the Audience API":
        for i, res in enumerate(audience_api_results):
            aud_csv = audience_insights_csv_1(res)
            audience_insights_file = open(args.results_file + aud_name + "/" + aud_name + "_audience_api_results_" + str(i) + ".piped", "w")
            audience_insights_file_json = open(args.results_file + aud_name + "/" + aud_name + "_audience_api_results_" + str(i) + ".json", "w")
            audience_insights_file_json.write(json.dumps(res).encode("utf-8"))
            audience_insights_file_json.close()
            for line in aud_csv:
                audience_insights_file.write(line[0].encode("utf-8") + " | " + str(int(line[1])) + "\n")
                if int(line[1]) > 15:
                    print line[0] + " | " + str(int(line[1]))
    else:
        print audience_api_results

    audience_insights_file.close()


