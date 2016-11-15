import unittest
import subprocess
import json

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

INPUT_FILE_NAME = 'dummy_tweets.json'

class AnalysisTests(unittest.TestCase):
    """Tests for the gnip_analysis_pipeline.enrichment package"""
    def setUp(self):
        # check input file via shell
        self.line_generator = open(INPUT_FILE_NAME)  
        p1 = subprocess.Popen(['cat',INPUT_FILE_NAME], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['wc', '-l'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        self.generator_length_truth, self.generator_length_err = int(out), err

        # get a generator over the test tweets
        self.tweets = [json.loads(line) for line in self.line_generator ]
        
    #
    # measurement tests
    #
    def test_tweet_counting(self):
        """ test the TweetCounter and ReTweetCounter """  
        tweet_counter = TweetCounter()
        retweet_counter = ReTweetCounter()
        n_retweets = 0
        for tweet in self.tweets:
            tweet_counter.add_tweet(tweet)
            retweet_counter.add_tweet(tweet) 
             
            if tweet['verb'] == 'share':
                n_retweets += 1
        
        self.assertEqual(tweet_counter.get()[0][0],self.generator_length_truth)  
        self.assertEqual(retweet_counter.get()[0][0],n_retweets)  

    def tearDown(self):
        if not self.line_generator.closed:
            self.line_generator.close()

if __name__ == '__main__':
    unittest.main()
