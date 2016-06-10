import sys
#import is
try:
    import ujson as json
except ImportError:
    import json
import logging
from collections import defaultdict
from simple_n_grams.simple_n_grams import SimpleNGrams
import uuid
import datetime

def weight_and_screennames():
    return {"weight": 0, "screennames": set([])}

logger = logging.getLogger("analysis")

def setup_analysis(conversation = False, audience = False):
    """create the results dictionary"""
    results = {
            "tweet_count": 0,
            "non-tweet_lines": 0,
            "tweets_per_user": defaultdict(int),
            #"user_id_to_screenname": 
    }
    if conversation:
        results["body_term_count"] = SimpleNGrams(
                char_lower_cutoff=3
                ,n_grams=1
                ,tokenizer="twitter"
                )
        results["hashtags"] = defaultdict(int)
        results["urls"] = defaultdict(int)
        results["number_of_links"] = 0
        results["utc_timeline"] = defaultdict(int)
        results["local_timeline"] = defaultdict(int)
        results["at_mentions"] = defaultdict(weight_and_screennames)
        results["in_reply_to"] = defaultdict(int)
        results["RT_of_user"] = defaultdict(weight_and_screennames)
        results["quote_of_user"] = defaultdict(weight_and_screennames)

    if audience:
        results["bio_term_count"] = SimpleNGrams(
                char_lower_cutoff=3
                ,n_grams=1
                ,tokenizer="twitter"
                )
        results["profile_locations_regions"] = defaultdict(int)
        results["audience_api"] = ""

    # in the future we could add custom fields by adding kwarg = func where func is agg/extractor and kwarg is field name
    
    return results

def analyze_tweet(tweet, results):
    """Add relevant data from a tweet to 'results'"""

    ######################################
    # fields that are relevant for user-level and tweet-level analysis
    # count the number of valid Tweets here
    # if it doesn't have at least a body and an actor, it's not a tweet
    try: 
        body = tweet["body"]
        userid = tweet["actor"]["id"][:15]
        results["tweet_count"] += 1
    except (ValueError, KeyError):
        if "non-tweet_lines" in results:
            results["non-tweet_lines"] += 1
        return

    # count the number of tweets from each user
    if "tweets_per_user" in results:
        results["tweets_per_user"][tweet["actor"]["id"][15:]] += 1
    
    #######################################
    # fields that are relevant for the tweet-level analysis
    # ------------------> term counts
    # Tweet body term count
    if "body_term_count" in results:
        results["body_term_count"].add(tweet["body"])

    # count the occurences of different hashtags
    if "hashtags" in results:
        if "hashtags" in tweet["twitter_entities"]:
            for h in tweet["twitter_entities"]["hashtags"]:
                results["hashtags"][h["text"].lower()] += 1
    
    # count the occurences of different top-level domains
    if ("urls" in results) and ("urls" in tweet["gnip"]):
        for url in tweet["gnip"]["urls"]:
            try:
                results["urls"][url["expanded_url"].split("/")[2]] += 1
            except (KeyError,IndexError):
                pass
    # and the number of links total
    if ("number_of_links" in results) and ("urls" in tweet["gnip"]):
        results["number_of_links"] += len(tweet["gnip"]["urls"])
    
    # -----------> timelines
    # make a timeline of UTC day of Tweets posted
    if "utc_timeline" in results:
        date = tweet["postedTime"][0:10]
        results["utc_timeline"][date] += 1

    # make a timeline in normalized local time (poster's time) of all of the Tweets
    if "local_timeline" in results:
        utcOffset = tweet["actor"]["utcOffset"]
        if utcOffset is not None:
            posted = tweet["postedTime"]
            hour_and_minute = (datetime.datetime.strptime(posted[0:16], "%Y-%m-%dT%H:%M") + 
                    datetime.timedelta(seconds = int(utcOffset))).time().strftime("%H:%M")
            results["local_timeline"][hour_and_minute] += 1
    
    # ------------> mention results
    # which users are @mentioned in the Tweet
    if "at_mentions" in results:
        for u in tweet["twitter_entities"]["user_mentions"]:
            # update the mentions with weight + 1 and 
            # list all of the screennames (in case a name changes)
            if u["id_str"] is not None:
                results["at_mentions"][u["id_str"]]["weight"] += 1 
                results["at_mentions"][u["id_str"]]["screennames"].update([u["screen_name"].lower()])
    
    # count the number of times each user gets replies
    if ("in_reply_to" in results) and ("inReplyTo" in tweet):
        results["in_reply_to"][tweet["inReplyTo"]["link"].split("/")[3].lower()] += 1

    # --------------> RTs and quote Tweet
    # count share actions (RTs and quote-Tweets)
    # don't count self-quotes or self-RTs, because that's allowed now
    if (("quote_of_user" in results) or ("RT_of_user" in results)) and (tweet["verb"] == "share"):
        # if it's a quote tweet
        if ("quote_of_user" in results) and ("twitter_quoted_status" in tweet["object"]):
            quoted_id = tweet["object"]["twitter_quoted_status"]["actor"]["id"][15:]
            quoted_name = tweet["object"]["twitter_quoted_status"]["actor"]["preferredUsername"]
            if quoted_id != tweet["actor"]["id"]:
                results["quote_of_user"][quoted_id]["weight"] += 1       
                results["quote_of_user"][quoted_id]["screennames"].update([quoted_name])
        # if it's a RT
        elif ("RT_of_user" in results):
            rt_of_name = tweet["object"]["actor"]["preferredUsername"].lower()
            rt_of_id = tweet["object"]["actor"]["id"][15:]
            if rt_of_id != tweet["actor"]["id"]:
                results["RT_of_user"][rt_of_id]["weight"] += 1 
                results["RT_of_user"][rt_of_id]["screennames"].update([rt_of_name])

    ############################################
    # actor-property qualities
    # ------------> bio terms
    if "bio_term_count" in results:
        if tweet["actor"]["id"][:15] not in results["tweets_per_user"]:
            try:
                if tweet["actor"]["summary"] is not None:
                    results["bio_term_count"].add(tweet["actor"]["summary"])
            except KeyError:
                pass
    
    # ---------> profile locations
    if "profile_locations_regions" in results:
        # if possible, get the user's address
        try:
            address = tweet["gnip"]["profileLocations"][0]["address"]
            country_key = address.get("country", "no country available")
            region_key = address.get("region", "no region available")
        except KeyError:
            country_key = "no country available"
            region_key = "no region available"
        results["profile_locations_regions"][country_key + " , " + region_key] += 1
    
def analyze_user_ids(user_ids,results, groupings = None):
    """ call to Audience API goes here """
    import audience_api as api

    if groupings is not None:
        use_groupings = groupings
    else:
        grouping_dict = {"groupings": {
            "gender": {"group_by": ["user.gender"]}
            , "location_country": {"group_by": ["user.location.country"]}
            , "location_country_region": {"group_by": ["user.location.country", "user.location.region"]}
            , "interest": {"group_by": ["user.interest"]}
            , "tv_genre": {"group_by": ["user.tv.genre"]}
            , "device_os": {"group_by": ["user.device.os"]}
            , "device_network": {"group_by": ["user.device.network"]}
            , "language": {"group_by": ["user.language"]}}}
        use_groupings = json.dumps(grouping_dict)

    results["audience_api"] = api.query_users(list(user_ids), use_groupings)

