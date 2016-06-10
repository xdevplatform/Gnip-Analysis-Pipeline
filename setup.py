from setuptools import setup, find_packages

setup(name='gnip_analysis_pipeline',
        packages=find_packages(),
        scripts=['gnip_analysis_pipeline/tweet_enricher.py', 
            'gnip_analysis_pipeline/tweet_time_series_builder.py', 
            'gnip_analysis_pipeline/tweet_evaluator.py'
            ],
        version='0.1',
        install_requires=['sngrams','matplotlib','pyyaml','requests','requests_oauthlib','pyfarmhash']
        )
