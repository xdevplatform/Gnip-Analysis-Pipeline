"""
This file is a place to store utilities for measurement creation,
as well as default configuration values.
"""



min_token_length = 4

try:
    from simple_n_grams.stop_words import StopWords
    stop_words = StopWords()
except ImportError:
    stop_words = []

def token_ok(token): 
    if len(token) < min_token_length:
        return False
    if stop_words[token]:
        return False
    return True

def term_comparator(term1, term2):
    t1 = term1.lower().strip(' ').rstrip(' ')
    t2 = term2.lower().strip(' ').rstrip(' ')
    return t1 == t2

