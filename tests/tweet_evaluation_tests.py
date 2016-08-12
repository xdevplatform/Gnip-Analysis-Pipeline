import unittest
import json
import os
import subprocess

from gnip_tweet_evaluation import analysis, output 

INPUT_FILE_NAME = 'dummy_tweets.json'

class AnalysisTests(unittest.TestCase):
    """Tests for the gnip_tweet_evaluation.analysis module"""
    def setUp(self):
        # check input file via shell
        self.line_generator = open(INPUT_FILE_NAME)  
        p1 = subprocess.Popen(['cat',INPUT_FILE_NAME], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['wc', '-l'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        self.generator_length_truth, self.generator_length_err = int(out), err

        # get a list of the test tweets
        self.tweets = analysis.deserialize_tweets( self.line_generator )
        
    #
    # test input file
    #
    def test_generator_length(self):
        """ check shell file length against python file object iteration"""
        self.assertEqual(len([_ for _ in self.line_generator]), self.generator_length_truth)
        self.assertEqual(None,self.generator_length_err) 

    #
    # conversation analyses
    #
    def test_conversation_length(self):
        """
        Test count of Tweets in analysis code against known number
        """
        # configure results structure
        results = analysis.setup_analysis(conversation=True)
        # is this id necessary for testing?
        #results["unique_id"] = "TEST"
        # run analysis code (including conversation) 
        analysis.analyze_tweets(self.tweets, results)
        # ground truth from setUp() 
        self.assertEqual(results['tweet_count'],self.generator_length_truth)

    def test_body_term_count(self):
        """ inject body with a predetermined number of test tokens """ 
        pass
        # configure results structure
        results = analysis.setup_analysis(conversation=True)
        # use counter for verification 
        counter = 1
        for tweet in self.tweets:
            addition = " test_term"*counter
            tweet['body'] += addition
            analysis.analyze_tweet(tweet, results) 
            counter += 1
        expected_test_count = int(next(results['body_term_count'].get_tokens())[0])
        self.assertEqual(expected_test_count, sum(range(counter)))

    def test_hashtag_count(self):
        """ inject hashtags with a predetermined number of test tokens """ 
        pass
        # configure results structure
        results = analysis.setup_analysis(conversation=True)
        # use counter for verification 
        counter = 0
        for tweet in self.tweets:
            tweet['twitter_entities']['hashtags'].append({"text":"notarandomhashtag"}) 
            analysis.analyze_tweet(tweet, results) 
            counter += 1
        self.assertEqual(results['hashtags']['notarandomhashtag'], counter)  

    #
    # audience analyses
    #
    def test_audience_length(self):
        pass
        # configure results structure
        results = analysis.setup_analysis(audience=True)
        # run analysis code (including audience) for user ids 
        analysis.analyze_tweets(self.tweets, results)  
        user_ids = results["tweets_per_user"].keys()

        # get ground truth (# unique user ids) from test data file
        p1 = subprocess.Popen(['cat', INPUT_FILE_NAME], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['python', '-c', 'import sys; import json; print(len(set([json.loads(i)["actor"]["id"] for i in sys.stdin])))'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        shell_user_count = int(out)
        self.assertEqual(shell_user_count, len(user_ids)) 

    def test_bio_term_count(self):
        """ inject bio with a predetermined number of test tokens """
        pass
        # configure results structure
        results = analysis.setup_analysis(audience=True)
        # use counter for verification 
        counter = 1
        for tweet in self.tweets:
            addition = " test_term"*counter
            tweet['actor']['summary'] += addition
            analysis.analyze_tweet(tweet, results) 
            counter += 1
        expected_test_count = int( next(results['bio_term_count'].get_tokens())[0] )
        self.assertEqual(expected_test_count, sum(range(counter)))

    #
    # stubs to fill out 
    #
    def test_weight_and_screennames(self):
        pass

    def test_setup_analysis(self):
        pass

    def test_tweets_per_user(self):
        pass

    def test_urls(self):
        pass

    def test_number_of_links(self):
        pass

    def test_utc_timeline(self):
        pass

    def test_local_timeline(self):
        pass

    def test_at_mentions(self):
        pass

    def test_in_reply_to(self):
        pass

    def test_quote_of_user(self):
        pass

    def test_rt_of_user(self):
        pass

    def test_profile_locations_regions(self):
        pass

    def test_analyze_user_ids(self):
        pass


    def tearDown(self):
        if not self.line_generator.closed:
            self.line_generator.close()

class OutputTests(unittest.TestCase):
    """Tests for the gnip_tweet.evaluation.output module"""
    def setUp(self):
        pass

    def test_flatten_dict(self):
        pass



if __name__ == '__main__':
    unittest.main()
