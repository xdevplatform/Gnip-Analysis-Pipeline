def split_tweets(tweets,splitting_config):
    analyzed_tweets = []
    baseline_tweets = []

    for tweet in tweets:
        if splitting_config['analyzed'](tweet):
            analyzed_tweets.append(tweet)
        if splitting_config['baseline'](tweet):
            baseline_tweets.append(tweet)

    return baseline_tweets,analyzed_tweets
