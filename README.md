# Overview

This repository contains a suite of Python scripts that reads JSON-formatted Tweet data,
enriches the tweet payloads with model-based metadata, builds time series based
on programmable counters, and returns CSV-formatted data. 

While this package contains to core elements of the pipeline, we have
placed many useful configuration tools in 
[Gnip-Analysis-Config](https://github.com/jeffakolb/Gnip-Analysis-Config).

# Installation

This package can be pip-installed:

`$ pip install gnip_analysis_pipeline`

The package can also be pip-installed locally from the cloned repository location:

`[REPOSITORY]$ pip install -e .`


# Core Pipeline Components

The pipeline abstracts the core, invariant pieces of an analysis of Tweet data.
We first _enrich_ individual Tweets with metadata. We can then create _time
series_ by counting things in time intervals. The time series creation can
be generalized to perform a variety of measurements on a set of Tweet payloads.

Because Tweet enrichment can be easily parallelized and because the resulting
metadata can be counted and evaluated, we usually enrich before counting and
evaluating. This is not strictly necessary, for example, when the Tweet analysis 
functions only on data in the original Gnip payload.

## Enrichment

In this step, we enrich individual Tweets with metadata, derived from the
current Tweet payload, potentially augmented by an external model.

We do enrichment by piping Tweet objects to the `tweet_enricher.py` script.

Enrichments are defined by classes that implement an `enrich` method,
which has one argument: the dictionary representing a Tweet. 
We configure enrichments by providing a valid Python file via the `-c` option
of the enriching script. To specify the enrichments to be run, 
this configuration file defines a list variable called `class_list`, which
contains a sequence of enrichment class definition objects. 
Because the configuration file is valid Python, enrichment classes 
can be defined locally or imported. 
See `example/my_enrichments.py` for an example.

Other examples and helper classes are in
the `gnip_analysis_config/enrichment/` directory of 
[Gnip-Analysis-Tools](https://github.com/jeffakolb/Gnip-Analysis-Tools/).

## Time Series Construction

In this step, we count objects found in the Tweet payload over a given time
bucket, and return a CSV-formatted representation of these counts.

We create time series data with the `tweet_time_series_builder.py` script.
Command-line options allow you to configure the size of the time bucket, 
and whether zero-count sums are returned.
By default, this script will parallelize the aggregation. You can control
this with the `-m` option, which specifies the maximum number of Tweets to 
be aggregated in a single process.

Counts of things are defined by measurement objects, which make one or more
counts of things found in the Tweet payloads. A measurement class must implement:

* `add_tweet(tweet)` - add Tweet data to measurement 
* `get()` - get the current state of the measurement
* `combine(other_measurement)` - combine measurement with another instance of the same measurement

It's optional but often useful to define a naming scheme and a `get_name`
(or equivalent) method.

As with enrichments, measurements are defined and configured with a
config file.  We configure which measurements to run via the
"measurement\_list" variable. See `example/my_measurements.py`.

Since we often want to define many measurement classes programatically,
we provide tools for this, and many examples, 
in the `gnip_analysis_config/measurement` directory of
[Gnip-Analysis-Tools](https://github.com/jeffakolb/Gnip-Analysis-Tools/).

## Trend Detection

To do trend detection on your resulting time series data, use
[Gnip-Trend-Detection](https://github.com/jeffakolb/Gnip-Trend-Detection),
which is designed to accept data from this pipeline.

# Example

This example assumes that you have installed the package in your Python 
environment, have cloned the repo,
and that you are working from a test directory called "TEST". 
From the `example` directory in the repo, copy 
`dummy_tweets.json` to your test directory.

A naive configuration of pipeline would look like:

`[TEST] $ cat dummy_tweets.json | tweet_enricher.py | tweet_time_series_builder.py > output.csv`

In fact, this produces no output, because the default behavior of the scripts is
to do nothing.

## Example configuration files

You can find two example configuration files in the `example` directory or the repo. 
Copy them to your TEST directory. They
should be used as arguments to the `-c` options of the enrichment and time
series scripts.

`[TEST] $ cat dummy_tweets.json | tweet_enricher.py -c my_enrichments.py |
tweet_time_series_builder.py -c my_measurements.py > time_series.csv`

The enrichment class in `my_enrichments.py` adds an enrichment called
TestEnrichment which always has the value of `1`. The classes in 
`my_measurements.py` define counter measurements for the number of 
Tweet (all Tweets) and for the number of Retweets.
