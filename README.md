# Overview

This repository contains a Python package that reads JSON-formatted Tweet data,
enriches the tweet payloads with model-based metadata, builds time series based
on programmable counters, and returns CSV-formatted data. A second package
performs audience and conversation analysis on sets of Tweets.

# Installation

This package can be pip-installed from the cloned repository location.

`$ pip install gnip_analysis_pipeline[nltk]`

where `nltk` installs the extra dependencies needed for sample NLTK enrichment.
You may also need to install [NLTK corpora](http://www.nltk.org/data.html).  

The package can also be pip-installed locally from the cloned repository location.

`[REPOSITORY]$ pip install -e .[nltk]`


# Core Pipeline Components

The pipeline abstracts the core, invariant pieces of an analysis of Tweet data.
We first _enrich_ individual Tweets with metadata. We can then create _time
series_ by counting things in time intervals. The time series creation can
be generalized to perform a variety of measurements on a set of Tweet payloads.

Because Tweet enrichment can be easily parallelized and because the resulting
metadata can be counted and evaluated, we usually enrich before counting and
evaluating. This is not strictly necessary, for example, when the Tweet analysis 
functions only on metadata in the original Gnip payload.

## Enrichment

In this step, we enrich individual Tweets with metadata, derived from the
current Tweet payload or from an external model.

We do enrichment by piping Tweet objects to the `tweet_enricher.py` script.

Enrichments are defined by classes that follow the pattern found in the modules
in `gnip_analysis_pipeline/enrichments/`, namely:

1. Enrichment classes typically inherit from `BaseEnrichment` in
`gnip_analysis_pipeline/enrichments/enrichment_base.py`. Enrichment classes
inheriting from `BaseEnrichment` must implement an `enrichment_value` method
that accepts at Tweet payload and returns the enrichment value. Alternately,
the enrichment class must define an `enrich` method that acts on a dictionary
representing a Tweet payload, and must attach the resulting metadata to the
payload. The base class manages and hides these actions. 

2. Enrichment modules must contain a "class\_list" variable which contains the
   names of the enrichment classes to be used.  Enrichment classes can be
disabled by removing their names from this list.

3. Enrichment modules are enabled by having their module name (without the
   trailing "\_enrichment.py") added to the "module\_name\_list" variable,
which had a default value in `tweet_enricher.py` and can be locally defined in
a module specified with the `-c` option. See `example/my_enrichments.py`

## Time Series Construction

In this step, we count objects found in the Tweet payload over a given time
bucket, and return a CSV-formatted representation of these counts.

We create time series data with the `tweet_time_series_builder.py` script.
Command-line options allow you to configure the size of the time bucket, 
and whether zero-count sums are returned.

Counts of things are defined by measurement objects, which make one or more
counts of things found in the Tweet payloads. We provide two simple examples of
measurement classes in `gnip_analysis_pipeline/measurements.py`. 
These are the default measurements. We've created
a more robust set of objects in `gnip_analysis_pipeline/measurement_base.py`,
including a base class the facilitates Tweet filtering, and a number of helper
classes for extracting various payload element and making different types of
counts.

As with enrichments, measurement can be defined and configured locally with a
config file.  We configure which measurements to run via the
"measurement\_list" variable. The same config file can be used to import base
classes and make local measurement class definitions variable. See
`example/my_measurements.py`.

## Trend Detection

To do trend detection on your resulting time series data, use
[Gnip-Trend-Detection](https://github.com/jeffakolb/Gnip-Trend-Detection),
which is designed to accept data from this pipeline.

# Example

This example assumes that you have installed the package in your Python 
environment, and that you are working from a test directory called "TEST". 
Copy the dummy data file at
`example/dummy_tweets.json` to your test directory.

A typical time series processing pipeline would look like:

`[TEST] $ cat dummy_tweets.json | tweet_enricher.py | tee enriched_dummy_tweets.json |
tweet_time_series_builder.py -bhour > dummy_tweets_hourly_time_series.csv`

This process runs the default enrichments (the 'test' enrichment) and the default
measurements ('TweetCounter' and 'ReTweetCounter'). Note that the dummy Tweets 
file contains no Retweets.

## Example configuration files

You can find two example configuration files in the `example` directory. Copy them to your
TEST directory. They
should be used as arguments to the `-c` option of the enrichment and time
series scripts, and to the `-s` option of the evaluation script.

`[TEST] $ cat dummy_tweets.json | tweet_enricher.py -c my_enrichments.py |
tweet_time_series_builder.py -c my_measurements.py > time_series.csv`

The file `my_enrichments.py` contains a redefinition of the `module_name_list`
variable. `my_measurements` contains a few new measurement class definitions:

* "CutoffBodyTermCounters" returns counts of all tokens found in the Tweet body
 where the count exceeds some cutoff. 

* "HashtagCounters" returns counts of all hashtags found.

These measurements, along with a simple tweet-counting measurement, are enabled with a
redefinition of the `measurements_list` variable. The count cutoff can also be
defined in this file.  

