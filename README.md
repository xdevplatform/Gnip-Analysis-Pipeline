# Overview

This software reads from JSON-formatted Tweet data,
enriches the tweets, makes aggregate measurements, builds time series,
performs trend detection on the time series, and prints out
a summary. 

# Core Pipeline Components

## Enrichments

Task: enrich individual Tweets with metadata, derived from the current Tweet 
payload or from an external model.

Write your enrichment class, following the example of `test_module.py`. 
To enable it, modify the "module_name_list" in `enricher.py`. 

## Aggregation

Task: make measurements on each tweet, and aggregate the measurements
across a time interval.

The measurements to be made are defined in `measurements.py`.
This file contains a list of class definitions. Classes must follow
the specified pattern. Measurement class instances are filled with results,
pickle-serialized, and sent to stdout. 

## Time Series Construction

Task: Build a CSV containing a time series for each aggregated measurement.

Use `series_builder.py` to construct time series from the aggregated data.
This will also produce a rules file that works with the 
Gnip-Trend-Detection software. 

## Trend Detection

Task: identify trends and spikes in time series.

This software uses the [Gnip-Trend-Detection](https://github.com/jeffakolb/Gnip-Trend-Detection) 
code to do the actual trend analysis of the point-by-point figure of merit. 
The script `detector.py` prints out a summary of spikes and trends.

## Other Components

Correlation coefficients between pairs of time series can be calculated
with `./correlations.py`. This will calculate a coefficient for all pairs
of time series found in the input CSV. Time series must be of equal length, 
which can be accomplished by using the `-e` flag of `aggregator.py`. This 
saves empty measurements. 

Insights into conversations and audiences can be generated with `insights.py`. 
This script takes a list of Tweet or user IDs and extracts the most 
prominent features of the data. For example, the audience insights include
the most common terms in the users' bios, while the conversation insights
include the most common hashtags.

# Example

Assume you have a file of JSON-formatted Tweet data, called `tweets.json`.
A typical enrichment and aggregation process would look like:

`$ cat tweets.json | ./enricher.py | tee enriched_tweets.json | ./aggregator.py > tweets.pkl`

Time series construction:

`$ ./series_builder.py -i tweets.pkl -o time_series.csv -r rules.json`

Trend detection (see [Gnip-Trend-Detection](https://github.com/jeffakolb/Gnip-Trend-Detection) for details).

`$ [GNIP-TREND-DETECTION-LOCATION]/analyze_all_rules.py -c trend_config.cfg -i data.csv -e data_analyzed.pkl -r -a -p`

`$ ./detector.py -t 1.0 data_analyzed.pkl`

Conversation insights:

`$ cat enriched_tweets.json | ./insights.py -c -f > conversation_insights.txt`

Correlations:

`$ ./correlations.py -i data.csv > correlations.txt`

# Parallel Processing

The `process_data.bash` script provides a template for running multiple pipelines
in parallel. 

# Utilities

There are a variety of utility scripts in the `utils` directory. 
