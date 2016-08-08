from setuptools import setup, find_packages

setup(name='gnip_analysis_pipeline',
        packages=find_packages(),
        scripts=['tweet_enricher.py', 
            'tweet_time_series_builder.py', 
            'tweet_evaluator.py',
            'user_id_evaluator.py'
            ],
        version='0.1',
        install_requires=['sngrams','matplotlib','pyyaml','requests','requests_oauthlib','pyfarmhash','nltk'] 
        )
