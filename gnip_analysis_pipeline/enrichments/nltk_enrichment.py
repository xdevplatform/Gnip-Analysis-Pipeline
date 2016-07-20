from enrichment_base import BaseEnrichment
from nltk.tokenize import SpaceTokenizer
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

class NLTKSpaceTokenizeBody(BaseEnrichment):
    def __init__(self):
        self.tokenizer = SpaceTokenizer()
    def enrichment_value(self,tweet):
        return self.tokenizer.tokenize(tweet['body'])
    def __repr__(self):
        return "Use the NLTK SpaceTokenizer to parse the Tweet body."

class NLTKWordTokenizeBody(BaseEnrichment):
    def __init__(self):
        self.tokenizer = word_tokenize
    def enrichment_value(self,tweet):
        return self.tokenizer(tweet['body'])
    def __repr__(self):
        return "Use the default NLTK word tokenizer to parse the Tweet body."

class NLTKPOSBody(BaseEnrichment):
    def __init__(self):
        self.tagger = pos_tag
    def enrichment_value(self,tweet):
        return self.tagger( tweet['enrichments']['NLTKWordTokenizeBody'] )
    def __repr__(self):
        return "Use the NLTK part-of-speech tagger on the Tweet body tokens."

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
    def __init__(self):
        self.tokenize = SpaceTokenizer().tokenize
    def __repr__(self):
        return "Use the NLTK SpaceTokenizer to parse the Tweet body."

class NLTKWordTokenizeBio(NLTKTokenizeBio):
    def __init__(self):
        self.tokenize = word_tokenize
    def __repr__(self):
        return "Use the default NLTK word tokenizer to parse the Tweet body."

class NLTKPOSBio(BaseEnrichment):
    def __init__(self):
        self.tagger = pos_tag
    def enrichment_value(self,tweet):
        return self.tagger( tweet['enrichments']['NLTKWordTokenizeBio'] )
    def __repr__(self):
        return "Use the NLTK part-of-speech tagger on the Tweet body tokens."

class_list = ["NLTKSpaceTokenizeBody"
        , "NLTKWordTokenizeBody"
        , "NLTKPOSBody"
        , 'NLTKSpaceTokenizeBio'
        , 'NLTKWordTokenizeBio'
        , 'NLTKPOSBio'
        ]
