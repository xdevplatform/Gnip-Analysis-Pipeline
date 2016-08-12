import collections
import operator
from .utils import token_ok, term_comparator

"""

This file is just a bunch of class definitions. Each class defines a 
measurement, which make one or more counts of things in the Tweet payload.

To work with the time series building code, each class must implement 
the following methods:
    add_tweet(dict: tweet)
    get()

The 'add_tweet' function is the entry point; it takes a dict representing a
JSON-formatted Tweet payload. The 'get' function is the exit; it returns a 
sequence of tuples of ( current count, count name). Any number of counts may
be managed by a single measurement class.

--------------------

MeasurementBase class

MeasurementBase is a convenient base class that defines 'add_tweet' such that the
measurement is only updated by tweets passing a set of filters, as defined
below.  If a tweet passes all filters, it is passed to the 'update' method,
which must be implemented in the child class. MeasurementBase also provides a
naming function, 'get_name'.

Configuration parameters (e.g. the minimum number of counts to return) are 
passed as keyword arguments to the constructor, and must be attached to the object
in all constructors.

Usage:

All classes inheriting from MeasurementBase must define or inherit the methods:
 - update(dict: tweet):
    udpates internal data store with Tweet info; no return value
 - get():
    returns a representation of internal data store

Measurements can be selectively applied to tweets by
defining the class member 'filters', which is a list of 3-tuples:
([list of JSON key names to access the Tweet element]
, comparison_function
, comparison_value).
Tweets will only be parsed if comparison_function(Tweet_element,comparison_value)
is true.


class naming convention: 
    classes that implement 'get' should contain 'Get' in the name
    classes defining counters should contain 'Counter' or 'Counters' in the name

"""
class MeasurementBase(object):
    """ 
    Base class for measurement objects.
    It implements 'get_name' and 'add_tweet'. 
    Note that 'add_tweet' calls 'update', 
    which must be defined in a derived class."""
    def get_name(self):
        return self.__class__.__name__
    def add_tweet(self,tweet):
        """ this method is called by the aggregator script, for each enriched tweet """
        def get_element(data, key_path):
            """ recursive helper function to get tweet elements """
            key = key_path[0]
            if len(key_path) == 1:
                return data[key]
            else:
                new_key_path = key_path[1:]
                obj = data[key]
                if isinstance(obj,list):
                    results = []
                    for o in obj:
                        results.append( get_element(o,new_key_path) )
                    return results
                else:
                    return get_element(obj,new_key_path)
        # return before calling 'update' if tweet fails any filter
        if hasattr(self,"filters"):
            for key_path,comparator,value in self.filters:
                data = get_element(tweet,key_path)
                if not comparator(data,value):
                    return 
        self.update(tweet)

class Counter(MeasurementBase):
    """ base class for any single integer counter """
    def __init__(self, **kwargs): 
        [setattr(self,key,value) for key,value in kwargs.items()]
        self.counter = 0
    def get(self):
        return [(self.counter,self.get_name())]

class Counters(MeasurementBase):
    """ base class for multiple integer counters """
    def __init__(self, **kwargs):
        [setattr(self,key,value) for key,value in kwargs.items()]
        self.counters = collections.defaultdict(int)
    def get(self):
        return [(count,name) for name,count in self.counters.items()]

# these classes provide 'get_tokens' methods for
# various tweet components

class TokenizedBody(object):
    """ provides a 'get_tokens' method for tokens in tweet body 
        assumes Stanford NLP or NLTK enrichment was run on Tweet body"""
    def get_tokens(self,tweet):
        good_tokens = [] 
        if 'BodyNLPEnrichment' in tweet['enrichments']:
            tokens = [token 
                    for sentence in tweet['enrichments']['BodyNLPEnrichment']['sentences'] 
                    for token in sentence ]
        elif 'NLTKSpaceTokenizeBody' in tweet['enrichments']:
            tokens = tweet['enrichments']['NLTKSpaceTokenizeBody']
        else:
            raise KeyError('No NLP enrichment found!')

        for token in tokens:
            if token_ok(token):
                good_tokens.append(token)
        return good_tokens
class TokenizedBio(object):
    """ provides a 'get_tokens' method for tokens in user bio 
        assumes Stanford NLP or NLTK enrichment was run on Tweet user bio"""
    def get_tokens(self,tweet):
        good_tokens = [] 
        if 'BioNLPEnrichment' in tweet['enrichments']:
            tokens = [token 
                    for sentence in tweet['enrichments']['BioNLPEnrichment']['sentences'] 
                    for token in sentence ]
        elif 'NLTKSpaceTokenizeBio' in tweet['enrichments']:
            tokens = tweet['enrichments']['NLTKSpaceTokenizeBio']
        else:
            raise KeyError('No NLP enrichment found!')

        for token in tokens: 
            if token_ok(token):
                good_tokens.append(token)
        return good_tokens

# these classes provide specialized 'get' methods
# for classes with 'counters' members

class GetTopCounts(object):
    """ provides a 'get' method that deals with top-n type measurements 
        must define a 'self.counters' variable """
    def get(self):
        if not hasattr(self,'top_k'):
            setattr(self,'top_k',20)
        sorted_top = list( reversed(sorted(self.counters.items(),key=operator.itemgetter(1))) ) 
        return [(count,name) for name,count in sorted_top[:self.top_k] ] 
class GetCutoffCounts(object):
    """ drops items with < 'min_n'/3 counts """
    def get(self):
        if not hasattr(self,'min_n'):
            setattr(self,'min_n',3)
        self.counters = { token:count for token,count in self.counters.items() if count >= self.min_n }
        return [(count,name) for name,count in self.counters.items() ]
class GetCutoffTopCounts(GetCutoffCounts):
    def get(self):
        if not hasattr(self,'top_k'):
            setattr(self,'top_k',20)
        self.counters = super(GetCutoffTopCounts).get()
        sorted_top = list( reversed(sorted(self.counters.items(),key=operator.itemgetter(1))) ) 
        return [(count,name) for name,count in sorted_top[:self.top_k] ]

# term counter helpers

class BodyTermCounters(Counters,TokenizedBody):
    """ provides an update method that counts instances of tokens in body """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            self.counters[token] += 1
class BioTermCounters(Counters,TokenizedBio):
    """ provides an update method that counts instances of tokens in bio"""
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            self.counters[token] += 1

class SpecifiedBodyTermCounters(Counters,TokenizedBody):
    """ base class for integer counts of specified body terms
    derived classes must define 'term_list' """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            for term in self.term_list:
                if term_comparator(token,term):
                    self.counters[term] += 1
class SpecifiedBioTermCounters(Counters,TokenizedBio):
    """ base class for integer counts of specified body terms
    derived classes must define 'term_list' """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            for term in self.term_list:
                if term_comparator(token,term):
                    self.counters[term] += 1

# top body term parent classes 

class AllBodyTerms(BodyTermCounters):
    pass
class TopBodyTerms(GetTopCounts,BodyTermCounters):
    pass
class CutoffBodyTerms(GetCutoffCounts,BodyTermCounters):
    pass
class CutoffTopBodyTerms(GetCutoffTopCounts,BodyTermCounters):
    pass

retweet_filter = (["verb"],operator.eq,"share")

class MentionCounters(Counters):
    def update(self,tweet):
        for mention in tweet["twitter_entities"]["user_mentions"]:
            self.counters[mention["name"]] += 1 
class TopMentions(GetTopCounts,MentionCounters):
    pass
class CutoffMentions(GetCutoffCounts,MentionCounters):
    pass
class CutoffTopMentions(GetCutoffTopCounts,MentionCounters):
    pass

class CutoffTopBioTermsUniqUser(GetCutoffTopCounts,Counters,TokenizedBio):
    def __init__(self, **kwargs):
        [setattr(self,key,value) for key,value in kwargs.items()]
        self.users = []
        super(CutoffTopBioTermsUniqUser,self).__init__()
    def update(self,tweet):
        if tweet['actor']['id'] not in self.users:
            for token in self.get_tokens(tweet):
                self.counters[token] += 1
            self.users.append(tweet['actor']['id'])

#
# NLP
#
class POSCounter(Counter):
    def get_pos(self,rep, pos="NN"):
        ans = []
        for s in rep["sentences"]:
            for i in range(len(s["tokens"])):
                if s["pos"][i] == pos:
                    ans.append(s["lemmas"][i])
        return ans  
class BodyNNCounter(POSCounter):
    def update(self,tweet):
        rep = tweet["enrichments"]["BodyNLPEnrichment"]
        ans = self.get_pos(rep,pos="NN")
        self.counter += len(ans)
class BodyNNPCounter(POSCounter):
    def update(self,tweet):
        rep = tweet["enrichments"]["BodyNLPEnrichment"]
        ans = self.get_pos(rep,pos="NNP")
        self.counter += len(ans)
class BodyDTCounter(POSCounter):
    def update(self,tweet):
        rep = tweet["enrichments"]["BodyNLPEnrichment"]
        ans = self.get_pos(rep,pos="DT")
        self.counter += len(ans)
