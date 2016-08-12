from .enrichment_base import BaseEnrichment
class TestEnrichment(BaseEnrichment):
    """
    This is a test enrichment class that simply adds a `1` 
    to every tweet, in the appropriate location in the JSON payload
    """
    def __init__(self):
        """
        Load and initialize any external models or data here
        """
        self.config = {}
    def enrichment_value(self,tweet):
        """ Calculate enrichment value """
        return 1

# this list specifies which classes to use for enrichment
class_list = ["TestEnrichment"]
