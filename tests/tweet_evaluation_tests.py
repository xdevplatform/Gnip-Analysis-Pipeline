import unittest
import json
import os
import subprocess

import gnip_tweet_evaluation
import evaluate_tweets

INPUT_FILE_NAME = 'dummy_tweets.json'

class InputTests(unittest.TestCase):
    def setUp(self):
        self.generator = open(INPUT_FILE_NAME)  
        p1 = subprocess.Popen(['cat',INPUT_FILE_NAME], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['wc', '-l'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out,err = p2.communicate()
        self.generator_length_truth, self.generator_length_err = int(out), err
    
    def test_generator_length(self):
        self.assertEqual(len([_ for _ in self.generator]),self.generator_length_truth)
        self.assertEqual(None,self.generator_length_err) 

    def test_conversation_length(self):
        conversation_results = {"unique_id": "TEST"}
        evaluate_tweets.run_analysis(self.generator, conversation_results, None)
        
        self.assertEqual(conversation_results['tweet_count'],self.generator_length_truth)
    
    def test_audience_length(self):
        audience_results = {"unique_id": "TEST"}
        user_ids = evaluate_tweets.run_analysis(self.generator, None, audience_results) 
        
        self.assertEqual(audience_results['tweet_count'],len(user_ids)) 

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        """ put test tweets into a list """
        self.tweets = []
        for line in open(INPUT_FILE_NAME):
            self.tweets.append(json.loads(line))

    def test_body_term_count(self):
        """ inject body with a predetermined number of test tokens """
        conversation_results = {"unique_id": "TEST"}
        counter = 1
        for tweet in self.tweets:
            addition = " test_term"*counter
            tweet['body'] += addition
            gnip_tweet_evaluation.analysis.analyze_tweet(tweet,conversation_results) 
            counter += 1
        expected_test_count = int(conversation_results['body_term_count'].get_tokens().next()[0])
        self.assertEqual(expected_test_count,sum(range(counter)))
        
    def test_bio_term_count(self):
        """ inject bio with a predetermined number of test tokens """
        audience_results = {"unique_id": "TEST"}
        counter = 1
        for tweet in self.tweets:
            addition = " test_term"*counter
            tweet['actor']['summary'] += addition
            gnip_tweet_evaluation.analysis.analyze_bio(tweet,audience_results) 
            counter += 1
        expected_test_count = int(audience_results['bio_term_count'].get_tokens().next()[0])
        self.assertEqual(expected_test_count,sum(range(counter)))

    def test_hashtag_count(self):
        conversation_results = {"unique_id": "TEST"}
        counter = 0
        for tweet in self.tweets:
            tweet['twitter_entities']['hashtags'].append({"text":"notarandomhashtag"}) 
            gnip_tweet_evaluation.analysis.analyze_tweet(tweet,conversation_results) 
            counter += 1
        self.assertEqual(conversation_results['hashtags']['notarandomhashtag'],counter)  

if __name__ == '__main__':
    unittest.main()
