import collections
import operator
import sys

# master list of class definitions
m = []

"""

This file is just a bunch of class definitions,
each of which defines a particular measurement..

All classes appended to "m" will be run on all tweets;
by calling the 'add_tweet' method. This method is defined
in MeasurementBase and applies any filters
as described below. If a tweet passes all filters, it is
passed to the 'update' method.

All classes inheriting from MeasurementBase must
define or inherit the methods:
 - update:
    udpates internal data store; no return value
 - get:
    returns a representation of internal data store

Measurements can be selectively applied to tweets by
defining the class member 'filters', which is a list of 3-tuples:
([list of JSON key names to access the Tweet element]
, comparison_function
, comparison_value).
Tweets will only be parsed if comparison_function(Tweet_element,comparison_value)
is true.
"""

#
#Helper functions:
#
def term_comparator(term1, term2):
    t1 = term1.lower().strip(' ').rstrip(' ')
    t2 = term2.lower().strip(' ').rstrip(' ')
    return t1 == t2

try:
    from simple_n_grams.stop_words import StopWords
    stop_words = StopWords()
except ImportError:
    stop_words = []

def token_ok(token):
    if len(token) < 3:
        return False
    if stop_words[token]:
        return False
    return True

#
# parent classes:
#
# naming convention: classes that inherit from MeasurementBase
# also have names that end in "Base".
# other parent classes do not
#
class MeasurementBase(object):
    """ 
    Base class for all measurement objects.
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

class SimpleCounterBase(MeasurementBase):
    """ base class for any single integer counter """
    def __init__(self):
        self.counter = 0
    def update(self,tweet):
        self.counter += 1
    def get(self):
        return self.counter

class SimpleCountersBase(MeasurementBase):
    """ base class for multiple integer counters """
    def __init__(self):
        self.counters = collections.defaultdict(int)
    def get(self):
        return self.counters

# these classes provide 'get_tokens' methods for
# various tweet components

class TokenizedBody(object):
    """ provides a 'get_tokens' method for tokens in tweet body 
        assumes Stanford NLP enrichment was run on Tweet body"""
    def get_tokens(self,tweet):
        tokens = [] 
        try:
            for sentence in tweet['enrichments']['BodyNLPEnrichment']['sentences']:
                for token in sentence["tokens"]:
                    if token_ok(token):
                        tokens.append(token)
        except TypeError,KeyError: 
            pass
        return tokens
class TokenizedBio(object):
    """ provides a 'get_tokens' method for tokens in user bio 
        assumes Stanford NLP enrichment was run on Tweet user bio"""
    def get_tokens(self,tweet):
        tokens = [] 
        try:
            for sentence in tweet['enrichments']['BioNLPEnrichment']['sentences']:
                for token in sentence["tokens"]:
                    if token_ok(token):
                        tokens.append(token)
        except TypeError,KeyError:
            pass
        return tokens

# these classes provide specialized 'get' methods
# for classes with 'counters' members

class TopCounts(object):
    """ provides a 'get' method that deals with top-n type measurements 
        must define a 'self.counters' variable """
    def get(self):
        k = 20
        sorted_top = [ tup for tup in reversed(sorted(self.counters.items(),key=operator.itemgetter(1))) ]
        return sorted_top[:k]
class CutoffTopCounts(TopCounts):
    """ drops items with < 10 counts """
    def get(self):
        for token,count in self.counters.items():
            if count < 20:
                del self.counters[token]
        return super(CutoffTopCounts,self).get()

# term counter bases

class BodyTermCountersBase(SimpleCountersBase,TokenizedBody):
    """ provides an update method that counts instances of tokens in body """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            self.counters[token] += 1
class BioTermCountersBase(SimpleCountersBase,TokenizedBio):
    """ provides an update method that counts instances of tokens in bio"""
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            self.counters[token] += 1

class SpecifiedBodyTermCountersBase(SimpleCountersBase,TokenizedBody):
    """ base class for integer counts of specified body terms
    derived classes must define 'term_list' """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            for term in self.term_list:
                if term_comparator(token,term):
                    self.counters[term] += 1
class SpecifiedBioTermCountersBase(SimpleCountersBase,TokenizedBio):
    """ base class for integer counts of specified body terms
    derived classes must define 'term_list' """
    def update(self,tweet):
        for token in self.get_tokens(tweet):
            for term in self.term_list:
                if term_comparator(token,term):
                    self.counters[term] += 1

# top body term parent classes 

class ExactTopBodyTerms(TopCounts,BodyTermCountersBase):
    pass
class CutoffTopBodyTerms(CutoffTopCounts,ExactTopBodyTerms):
    pass
class ExactTopBioTerms(TopCounts,BioTermCountersBase):
    pass
class CutoffTopBioTerms(CutoffTopCounts,ExactTopBioTerms):
    pass

#
# simple global counters  
#
class TweetCounter(SimpleCounterBase):
    pass
m.append(TweetCounter)

retweet_filter = (["verb"],operator.eq,"share")
class ReTweetCounter(SimpleCounterBase):
    def __init__(self):
        self.filters = [retweet_filter] 
        super(ReTweetCounter,self).__init__()
m.append(ReTweetCounter)

#
# user mentions 
#
class MentionCounter(TopCounts,SimpleCountersBase):
    def update(self,tweet):
        for mention in tweet["twitter_entities"]["user_mentions"]:
            self.counters[mention["name"]] += 1 
class CutoffTopMentions(CutoffTopCounts,MentionCounter):
    pass

class CutoffTopBioTermsUniqUser(CutoffTopCounts,SimpleCountersBase,TokenizedBio):
    def __init__(self):
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
class POSCounter(SimpleCounterBase):
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

##
# generate measurements per rule, per topic model, etc.
##

# tuples of (rule tag, rule name)
# the rule name is arbitrary and will be included in the measurement class name
rules = [
        ## (RULE_TAG, RULE_NAME)
        ]

# specified terms to count occurences of 
term_list = []

##
# loop over PowerTrack rules 
##
for rule_tag,rule_name in rules:
    
    rule_filter = (["gnip","matching_rules","tag"], operator.contains, rule_tag)

    # tweet count
    cls_name = rule_name + "RuleCounter"
    cls_def = type(cls_name, (SimpleCounterBase,), {"filters": [rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)

    ## retweet counts 
    cls_name = rule_name + "RuleRetweetCounter"
    cls_def = type(cls_name,
            (SimpleCounterBase,),
            {"filters": [rule_filter, retweet_filter] }
            )
    globals()[cls_name] = cls_def
    m.append(cls_def)
    
    # top mentions
    cls_name = rule_name + "RuleCutoffTopMentions"
    cls_def = type(cls_name, (CutoffTopMentions,), {"filters": [rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)

    # top body terms
    cls_name = rule_name + "RuleCutoffTopBodyTerms"
    cls_def = type(cls_name, (CutoffTopBodyTerms,), {"filters": [rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)

    # top bio terms per uniq user
    cls_name = rule_name + "RuleCutoffTopBioTermsUniqUser"
    cls_def = type(cls_name, (CutoffTopBioTermsUniqUser,), {"filters": [rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)

    # parts of speech in body
    cls_name = rule_name + "RuleBodyNNCounter"
    cls_def = type(cls_name, (BodyNNCounter,), {"filters":[rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)
    cls_name = rule_name + "RuleBodyNNPCounter"
    cls_def = type(cls_name, (BodyNNPCounter,), {"filters":[rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)
    cls_name = rule_name + "RuleBodyDTCounter"
    cls_def = type(cls_name, (BodyDTCounter,), {"filters":[rule_filter] })
    globals()[cls_name] = cls_def
    m.append(cls_def)

