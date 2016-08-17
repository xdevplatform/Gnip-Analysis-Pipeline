# Introduction

The code in this package evaluates sets of Tweets. It performs conversation
analysis by aggregating information from the Tweet bodies, and audience
analysis by aggregating user information found in the Tweet payload.

# Installation

The Tweet evaluation code is packaged as part of the Gnip-Analysis-Pipeline
package, which can be pip-installed:

`$ pip install gnip_analysis_pipeline`

The Tweet evaluation code has its own package, `gnip_tweet_evaluation`. If you
wish to create plots in your output, you should install the extra dependencies:

`$ pip install gnip_analysis_pipeline[plotting]`

# Package Structure

Once `gnip_analysis_pipeline` has been pip-installed, you will have two
relevant scripts in your path: `tweet_evaluator.py` and `user_id_evaluator.py`.
These command-line tools are the primary interfaces to the package.
`tweet_evaluator.py` performs audience and conversation analysis (including a
call to the Gnip Audience API) on a set of Tweets, while `user_id_evaluator.py`
acts on a set of Twitter user IDs and simple runs them through the Audience
API.

The analysis code is factored into an analysis module, an output module, and a
module that contains the Audience API interface. 

## Detailed Description

A typical, _absolute_ analysis starts by configuring a "results" dictionary
with `analysis.setup_analysis`. _Relative_ analyses, which report the difference
between the analyses of two different input data sets, are described below.

The primary interface for a list of Tweets and a configured "results" object is
the `analysis.analyze_tweets` function, which handles the iteration over
Tweets, and manages the multiple analyses needed for a relative analysis. This
function assumes that the Tweets are deserialized into dictionary
representations, which is accomplished with the generator function
`analysis.deserialize_tweets`.

Within the `analyze_tweets` function, individual Tweet data is aggregated into
the results object(s) with the `analyze_tweet` function. We then extract unique
user IDs from the results and pass them to the Audience API interface.

# Audience API Interface

We assume that most users simply want to pass a set of user IDs to the API and
retrieve a specified set of demographic data (called "groupings" in the
[docs](http://support.gnip.com/apis/audience_api/)).  We provide this interface
with the `user_ids_evaluator.py` script.  This script handles input and calls
`analysis.analyze_user_ids`, which defines a default grouping set, and handles
a multiple-audience, relative analysis.  

The interface to the Gnip API itself is designed so that subsequent queries for
an already-analyzed list of user IDs don't create new segments and audiences.
The groupings and user IDs get passed to the API in the
`audience_api.query_users` function. This function encapsulates the following
actions:
* De-duplicate, sort, and hash the input list of user IDs to form a unique
  identifier for that set of user IDs.
* Split the user ID list into sufficiently small chunks for segment creation.
If the ID list is long enough to require more than one segment, the segment
base name is the unique identifier and an index is appended to the name.
* Check for the existence of segments named with the unique identifier, which
  would indicate that the user ID list has been previously processed. Only
create new segment(s) and upload IDs if the segment or segments do not exist.
* Check for the existence of an audience named with the unique identifier. If
  it exists, query it for the specified groupings. If it doesn't exist, create
it, associate it with the appropriate segments, and query it.
* Return the query results.

The `output` module handles the formatting and display of the results.

# Relative Analyses

All interfaces handle relative analyses, in which two sets of Tweets or two
sets of user IDs are specified, and the relative difference between their
analysis results is returned (only implemented for Audience API results, for
now).  We define these two input data sets with a "splitting configuration",
which can be passed as a command-line argument. This configuration defines two
function: the "analyzed" function, which returns the set of Tweets of interest,
and a "baseline" function, which returns a set of Tweets against which the
"analyze" Tweet results are compared.
