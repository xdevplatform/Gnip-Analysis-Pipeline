import collections

# counter configuration

# add measurement definitions to this list to activate
measurements_list = []

# these measurement class definitions are explicit, and do
# not inherit from MeasurementBase
class TweetCounter(object):
    def __init__(self, **kwargs):
        self.counter = 0
    def add_tweet(self,tweet):
        self.counter += 1
    def get(self):
        return [(self.counter,self.get_name())]
    def get_name(self):
        return 'TweetCounter'

class ReTweetCounter(object):
    def __init__(self, **kwargs):
        self.counter = 0
    def add_tweet(self,tweet):
        if tweet['verb'] == 'share':
            self.counter += 1
    def get(self):
        return [(self.counter,self.get_name())]
    def get_name(self):
        return 'ReTweetCounter'

measurements_list.extend([TweetCounter, ReTweetCounter])
