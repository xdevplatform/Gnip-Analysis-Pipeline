class TweetCounter(object):
    def __init__(self, **kwargs):
        self.counter = 0
    def add_tweet(self,tweet):
        self.counter += 1
    def get(self):
        return [(self.counter,self.get_name())]
    def get_name(self):
        return 'TweetCounter'
    def combine(self,new):
        self.counter += new.counter

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
    def combine(self,new):
        self.counter += new.counter

measurement_class_list = [TweetCounter, ReTweetCounter]
