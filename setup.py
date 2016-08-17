from setuptools import setup, find_packages

setup(name='gnip_analysis_pipeline',
        packages=find_packages(),
        scripts=['tweet_enricher.py', 
            'tweet_time_series_builder.py', 
            'tweet_evaluator.py',
            'user_id_evaluator.py'
            ],
        version='0.1',
        license='MIT',
        author='Jeff Kolb',
        author_email='jeffakolb@gmail.com',
        description='A processing pipeline for enriching and aggregating Tweet data from Twitter APIs',
        url='https://github.com/jeffakolb/Gnip-Analysis-Pipeline',
        install_requires=['sngrams','pyyaml','requests','requests_oauthlib','pyfarmhash']  ,
        extras_require={'plotting':['matplotlib'],'nltk':['nltk']}
        )
