from .enrichment_base import BaseEnrichment
from nltk.tokenize import SpaceTokenizer
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

class NLTKSpaceTokenizeBody(BaseEnrichment):
    """Use the NLTK SpaceTokenizer to parse the Tweet body."""
    def __init__(self):
        self.tokenizer = SpaceTokenizer()
    def enrichment_value(self,tweet):
        return self.tokenizer.tokenize(tweet['body'])

class NLTKWordTokenizeBody(BaseEnrichment):
    """Use the default NLTK word tokenizer to parse the Tweet body."""
    def __init__(self):
        self.tokenizer = word_tokenize
    def enrichment_value(self,tweet):
        return self.tokenizer(tweet['body'])

class NLTKPOSBody(BaseEnrichment):
    """Use the NLTK part-of-speech tagger on the Tweet body tokens."""
    def __init__(self):
        self.tagger = pos_tag
    def enrichment_value(self,tweet):
        return self.tagger( tweet['enrichments']['NLTKWordTokenizeBody'] )

class NLTKTokenizeBio(BaseEnrichment):
    def enrichment_value(self,tweet):
        """ 
        Account for the fact that:
            - user bio can be None 
            - user bio can be non-existent (key doesn't exist) 
        """
        try:
            bio = tweet['actor']['summary']
        except KeyError:
            return []
        if bio is not None:
            return self.tokenize(bio)  
        else:
            return []
    
class NLTKSpaceTokenizeBio(NLTKTokenizeBio): 
    """Use the NLTK SpaceTokenizer to parse the Tweet body."""
    def __init__(self):
        self.tokenize = SpaceTokenizer().tokenize

class NLTKWordTokenizeBio(NLTKTokenizeBio):
    """Use the default NLTK word tokenizer to parse the Tweet body."""
    def __init__(self):
        self.tokenize = word_tokenize

class NLTKPOSBio(BaseEnrichment):
    """Use the NLTK part-of-speech tagger on the Tweet body tokens."""
    def __init__(self):
        self.tagger = pos_tag
    def enrichment_value(self,tweet):
        return self.tagger( tweet['enrichments']['NLTKWordTokenizeBio'] )

class_list = ["NLTKSpaceTokenizeBody"
        , "NLTKWordTokenizeBody"
        , "NLTKPOSBody"
        , 'NLTKSpaceTokenizeBio'
        , 'NLTKWordTokenizeBio'
        , 'NLTKPOSBio'
        ]
