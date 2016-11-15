import unittest
import subprocess
import json

class TestEnrichment(object):
    def enrich(self,tweet):
        if 'enrichments' not in tweet:
            tweet['enrichments'] = {}
        tweet['enrichments'][self.__class__.__name__] = 1

INPUT_FILE_NAME = 'dummy_tweets.json'

class AnalysisTests(unittest.TestCase):
    """Tests for functions in tweet_enricher.py"""
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
    # test input file
    #
    def test_generator_length(self):
        """ check shell file length against python file object iteration"""
        self.assertEqual(len(self.tweets), self.generator_length_truth)
        self.assertEqual(None,self.generator_length_err) 

    #
    # enrichment
    #
    def test_test_enrichment(self):
        """ test the enrichment defined in test_enrichment.py """ 
        enrichment_cls = TestEnrichment()
        enriched_tweets = []
        for tweet in self.tweets:
            enrichment_cls.enrich(tweet)
            enriched_tweets.append(tweet)
        self.assertTrue(all(tweet['enrichments']['TestEnrichment']==1 for tweet in enriched_tweets))

    def tearDown(self):
        if not self.line_generator.closed:
            self.line_generator.close()

if __name__ == '__main__':
    unittest.main()
