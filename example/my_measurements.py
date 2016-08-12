from gnip_analysis_pipeline.measurement.sample_measurements import TweetCounter
from gnip_analysis_pipeline.measurement.measurement_base import *

class CutoffBodyTermCounters(GetCutoffCounts,TokenizedBody,Counters):
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            self.counters[token] += 1

class HashtagCounters(Counters):
    def update(self,tweet):
        for item in tweet['twitter_entities']['hashtags']:
            # put a # in from of the term, 
            # since they've been removed in the payload
            self.counters['#'+item['text']] += 1

measurements_list = [
        TweetCounter,
        HashtagCounters,
        CutoffBodyTermCounters,
        ]

config_kwargs = {}
config_kwargs['min_n'] = 3
