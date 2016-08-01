"""
This file is a place to store utilities for measurements,
as well as default configuration values.
"""



try:
    from simple_n_grams.stop_words import StopWords
    stop_words = StopWords()
except ImportError:
    stop_words = []

def token_ok(token, min_token_length = 4, stop_words = stop_words): 
    """ return whether the token str meets our quality criteria """
    if len(token) < min_token_length:
        return False
    if stop_words[token]:
        return False
    return True

def term_comparator(term1, term2):
    t1 = term1.lower().strip(' ').rstrip(' ')
    t2 = term2.lower().strip(' ').rstrip(' ')
    return t1 == t2

def sanitize_string(input_str):
    output_str = input_str
    return output_str
