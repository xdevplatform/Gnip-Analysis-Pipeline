from setuptools import setup, find_packages

setup(name='gnip_analysis_pipeline',
        packages=find_packages(),
        scripts=['tweet_enricher.py', 
            'tweet_time_series_builder.py', 
            ],
        version='0.4',
        license='MIT',
        author='Jeff Kolb',
        author_email='jeffakolb@gmail.com',
        description='A processing pipeline for enriching and aggregating Tweet data from Twitter APIs',
        extras_require = {'nltk' : 'nltk'},
        url='https://github.com/jeffakolb/Gnip-Analysis-Pipeline',
        )
