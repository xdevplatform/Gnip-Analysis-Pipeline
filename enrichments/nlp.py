import sys

"""
Requires:
- Stanford Core NLP
- stanford_corenlp_pywrapper
"""

try:
    sys.path.insert(0,"/home/jkolb/stanford_corenlp_pywrapper")
    from stanford_corenlp_pywrapper import CoreNLP
except ImportError:
    sys.stderr.write("Please install 'stanford_corenlp_pywrapper' and add to your sys.path\n")
    sys.exit(1)

from enrichment_base import BaseEnrichment

class BodyNLPEnrichment(BaseEnrichment):
    """
    """
    def __init__(self):
        """
        Load and initialize any external models or data here
        """
        self.corenlp = CoreNLP("pos", corenlp_jars=["/home/jkolb/stanford-corenlp-full-2015-04-20/*"])
    def enrichment_value(self,tweet):
        """ Calculate enrichment value """
        rep = self.corenlp.parse_doc(tweet["body"])
        return rep

    def __repr__(self):
        """ Add a description of the class's function here """
        return("Stanford core NLP applied to tweet body")

class BioNLPEnrichment(BaseEnrichment):
    """
    """
    def __init__(self):
        """
        Load and initialize any external models or data here
        """
        self.corenlp = CoreNLP("pos", corenlp_jars=["/home/jkolb/stanford-corenlp-full-2015-04-20/*"])
    def enrichment_value(self,tweet):
        """ Calculate enrichment value """
        rep = self.corenlp.parse_doc(tweet["actor"]["summary"])
        return rep

    def __repr__(self):
        """ Add a description of the class's function here """
        return("Stanford core NLP applied to user bio")

class_list = ["BodyNLPEnrichment","BioNLPEnrichment"]
