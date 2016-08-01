
class BaseEnrichment(object):
    """ 
    Classes that add data to a single tweet (enrichments)
    inherit from this class. These derived enrichment classes
    must implement the function 'enrichment value', which
    accepts a tweet dictionary as the single argument, and
    returns the enrichment value. This value must be JSON-
    serializable.
    """
    def enrich(self,tweet):
        """ this function is called by tweet_enricher.py"""
        if "enrichments" not in tweet:
            tweet['enrichments'] = {}
        tweet['enrichments'][self.__class__.__name__] = self.enrichment_value(tweet)


