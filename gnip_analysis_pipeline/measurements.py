
# simple measurement examples

m = []

class TweetCounter(object):
    def __init__(self):
        self.counter = 0
    def add_tweet(self,tweet):
        self.counter += 1
    def get(self):
        return self.counter
    def get_name(self):
        return 'TweetCounter'

class ReTweetCounter(object):
    def __init__(self):
        self.counter = 0
    def add_tweet(self,tweet):
        if tweet['verb'] == 'share':
            self.counter += 1
    def get(self):
        return self.counter
    def get_name(self):
        return 'ReTweetCounter'

m.extend([TweetCounter, ReTweetCounter])
