import sys
import logging
import json
import os
import datetime
from collections import defaultdict
from math import ceil
from matplotlib import use
use('Agg')
import matplotlib.pyplot as plt
from matplotlib import dates, use

logger = logging.getLogger('output')

if sys.version_info[0] < 3: 
    try:
        sys.setdefaultencoding('utf-8') 
    except AttributeError:
        pass

def top_terms_output(ngrams_object, title, output_path_base):
    """ output top terms from the ngrams object"""
    sys.stdout.write("\n\n")
    sys.stdout.write(ngrams_object.get_repr(10))
    
    top_tweet_terms_file = open(output_path_base + title + '.txt', 'w')
    top_terms = ngrams_object.get_repr()
    top_tweet_terms_file.write(top_terms.encode('utf-8'))
    top_tweet_terms_file.close()

def user_frequency_output(counts_dict, title, quantity, output_path_base):
    """ output of user frequency with ids and screennames """
    # take the dictionary counts_dict and sort its items by most to least frequent
    # counts_dict looks like: {<some user id>: {"weight": _, "screeennames": set([___])}, ... }
    user_frequencies = sorted(counts_dict.items(), key=lambda x: x[1]["weight"], reverse=True)
    list_of_output_strings = [str(x[1]["weight"])+', '+x[0]+' ,'+' ,'.join(list(x[1]["screennames"])) for x in user_frequencies]
    
    sys.stdout.write('\n\n{}, user id, username(s)\n'.format(quantity))
    sys.stdout.write("\n".join(list_of_output_strings[0:10]))
    
    user_freq_file = open(output_path_base + title + '.txt', 'w')
    user_freq_file.write('{}, user id, username(s)\n'.format(quantity))
    user_freq_file.write("\n".join(list_of_output_strings))
    user_freq_file.close()

def count_frequency_output(counts_dict, title, quantity, item, output_path_base):
    """ output frequency counts """
    # counts_dict looks like: {item: quantity}
    frequencies = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)
    list_of_output_strings = [ unicode(x[1]) + ', ' + x[0] for x in frequencies ]
    
    sys.stdout.write("\n\n{}, {}\n".format(quantity, item))
    sys.stdout.write("\n".join(list_of_output_strings[0:10]))
    
    freq_file = open(output_path_base + title + '.txt', 'w')
    freq_file.write("{}, {}\n".format(quantity, item))
    freq_file.write("\n".join(list_of_output_strings))
    freq_file.close()

def count_output(count, title, output_path_base):
    """ print counts """
    sys.stdout.write("\n\n{}\n".format(title))
    sys.stdout.write(str(count) + "\n")
    
    freq_file = open(output_path_base + title + '.txt', 'w')
    freq_file.write("{}\n".format(count))
    freq_file.write(str(count) + "\n")
    freq_file.close()

def local_timeline_plot(minute_dict, title, output_path_base):
    """ plot timeline of users Tweeting, hour granularity, local time """
    minute = minute_dict.items()
    hour_dict = defaultdict(int)
    for key, value in minute_dict.items():
        hour_dict[key.split(':')[0]] += value
    hour = hour_dict.items()
    times_values = sorted([ (datetime.datetime.strptime(x[0], '%H'), x[1]) for x in hour ], key=lambda x: x[0])
    times = [ x[0] for x in times_values ]
    values = [ x[1] for x in times_values ]
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 4))
    ax.plot(times, values)
    ax.set_xlabel("Users' local time", size=14)
    ax.set_ylabel('Tweets per hour', size=16)
    ax.set_title('When users Tweet during the day (based on local time)', size=14)
    ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()
    fig.savefig(output_path_base + title + '.png')

def utc_timeline_plot():
    """ plot timeline of users Tweeting, day graularity, UTC"""
    pass

def audience_api_output(audience_api_results, output_path_base):
    """ format the audience API results """
    print('\n\nAudience API Results')
    audience_api_file = open(output_path_base + '_audience_api.txt','w')
    if 'error' not in audience_api_results:
        for i, (grouping_name, grouping_result) in enumerate(audience_api_results.items()):
            print('\n' + grouping_name + '\n' + '-' * len(grouping_name))
            audience_api_file.write('\n' + grouping_name + '\n' + '-' * len(grouping_name) + '\n')
            
            if 'errors' in grouping_result:
                print( grouping_result['errors'][0] )
                audience_api_file.write(grouping_result['errors'][0])
            else:
                def expand(key, value):
                    if isinstance(value, dict):
                        return [ (key + ' | ' + k, v) for k, v in flatten_dict(value).items() ]
                    elif isinstance(value, list):
                        return ['why is this happening??'] 
                    else:
                        return [(key, value)]

                flattened_result = dict([ item for k, v in grouping_result.items() for item in expand(k, v) ])
                flattened_tuples = flattened_result.items()
                grouping_result_csv = sorted(flattened_tuples, key=lambda x: (x[0].split('|')[0], -1 * float(x[-1])))
                
                for line in grouping_result_csv:
                    print(line[0] + ' | ' + str(line[1]) )
                    audience_api_file.write(line[0] + ' | ' + str(line[1]) + '\n' )
    else:
        print('Error: ' + audience_api_results['error'])
        audience_api_file.write('Error: ' + audience_api_results['error'])

def flatten_dict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + ' | ' + k, v) for k, v in flatten_dict(value).items() ]
        else:
            return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def dump_results(results, output_path, uid):
   
    try:
        os.stat(output_path) 
    except:
        os.makedirs(output_path)
    
    output_file_base = output_path.rstrip('/') + '/' + uid + '_'

    if "tweet_count" in results:
        count_output(results["tweet_count"], 
                "tweet_count", output_file_base)

    if "body_term_count" in results:
        top_terms_output(results["body_term_count"], 
                "top_tweet_terms", output_file_base)
    
    if "RT_of_user" in results:
        user_frequency_output(results["RT_of_user"], 
                "retweeted_users", "number of retweets", output_file_base)

    if "at_mentions" in results:
        user_frequency_output(results["at_mentions"], 
                "at_mentioned_users", "number of time mentioned", output_file_base)

    if "in_reply_to" in results:
        count_frequency_output(results["in_reply_to"], 
                "replied_to_users", "number of times replied to", "username", output_file_base)
    
    if "hashtags" in results:
        count_frequency_output(results["hashtags"], 
                "hashtags", "number of times tweeted", "hashtag", output_file_base)
    
    if "local_timeline" in results:
        local_timeline_plot(results["local_timeline"], 
                "local_timeline", output_file_base)
    
    if "utc_timeline" in results:
        utc_timeline_plot()

    if "number_of_links" in results:
        count_output(results["number_of_links"], "number_of_links", output_file_base)

    if "urls" in results:
        count_frequency_output(results["urls"], 
                "urls", "number of times tweeted", "base url", output_file_base)

    if "tweets_per_user" in results:
        count_frequency_output(results["tweets_per_user"], 
                "tweets_per_userid", "number of times tweeting", "user id", output_file_base)

    if 'bio_term_count' in results:
        top_terms_output(results["bio_term_count"], 
                "top_bio_terms", output_file_base)
        
    if 'profile_locations_regions' in results:
        count_frequency_output(results["profile_locations_regions"], 
                "profile_locations", "number of occurences", "country, region", output_file_base)

    if "audience_api" in results:
        audience_api_output(results["audience_api"], output_file_base)

    sys.stdout.write('\n\n')
