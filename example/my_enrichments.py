
class TestEnrichment(object):
    """
    This dummy enrichment class ensures that the Tweet contains a top-level key
    called 'enrichments', and assigns a 'TestEnrichment:1' key-value pair to
    that dictionary.
    """
    def enrich(self,tweet):
        if 'enrichments' not in tweet:
            tweet['enrichments'] = {}
        tweet['enrichments'][self.__class__.__name__] = 1

class_list = [TestEnrichment]
