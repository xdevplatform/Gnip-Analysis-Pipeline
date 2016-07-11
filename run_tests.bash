#!/bin/bash

# this is just a convenience script to make sure the
# data file for the tests can be found.

# copy the data file over to where the tests expect it it be
cp example/dummy_tweets.json .

# run all the tests
python tests/tweet_evaluation_tests.py

# remove the copy of the data
rm dummy_tweets.json
