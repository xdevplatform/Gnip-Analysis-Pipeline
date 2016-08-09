# Testing and development

Before submitting a pull request on bug fixes or new features, be sure to run the tests here in the test suite. Follow the steps below (example code follows):

- create an empty, isolated Python 2.7.11 environment 
- navigate to the repository root (``Gnip-Analysis-Pipeline``) and install the local version of the library. Use the ``-U`` flag to be sure that any pre-existing version is uninstalled and a fresh version is installed 
- run the test suite with `run_tests.bash`
- fix any errors from failed tests
- if you discover a new edge case, add it as a new test method where ever seems most appropriate

An example of how to install the library for development and testing:

```bash
jmontague@data-science-4:~ 
$ mkvirtualenv -p /opt/bin/python2.7 dev-env

(dev-env) jmontague@data-science-4:~ 
$ cd Gnip-Analysis-Pipeline/

(dev-env) jmontague@data-science-4:~/Gnip-Analysis-Pipeline [tests]
$ pip install . -U  # installs (and upgrades) all the dependencies
(dev-env) jmontague@data-science-4:~/Gnip-Analysis-Pipeline [tests]
$ ./run_tests.bash
....................
----------------------------------------------------------------------
Ran 20 tests in 6.024s

OK
```

If any of the tests fail, it's useful to use a second session (window) to edit the code and address the failing test. Then, when you're ready, you can hop back to the first session and run the reinstall (and upgrade) and tests all at once: 

```
(dev-env) jmontague@data-science-4:~/Gnip-Analysis-Pipeline/tests [tests]
$ cd ..; pip install . -U; cd -; python tweet_evaluation_tests.py 
Processing /mnt/home/jmontague/Gnip-Analysis-Pipeline
Requirement already up-to-date: sngrams in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: matplotlib in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: pyyaml in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: requests in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: requests_oauthlib in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: pyfarmhash in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from gnip-analysis-pipeline==0.1)
Requirement already up-to-date: pytz in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from matplotlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: cycler in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from matplotlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: python-dateutil in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from matplotlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: pyparsing!=2.0.0,!=2.0.4,>=1.5.6 in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from matplotlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: numpy>=1.6 in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from matplotlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: oauthlib>=0.6.2 in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from requests_oauthlib->gnip-analysis-pipeline==0.1)
Requirement already up-to-date: six in /mnt/home/jmontague/.virtualenvs/dev-env/lib/python2.7/site-packages (from cycler->matplotlib->gnip-analysis-pipeline==0.1)
Building wheels for collected packages: gnip-analysis-pipeline
  Running setup.py bdist_wheel for gnip-analysis-pipeline ... done
  Stored in directory: /home/jmontague/.cache/pip/wheels/82/40/69/105ba9587759164aa652e6737ba1cddabe3183cbb2f6d2f0f7
Successfully built gnip-analysis-pipeline
Installing collected packages: gnip-analysis-pipeline
  Found existing installation: gnip-analysis-pipeline 0.1
    Uninstalling gnip-analysis-pipeline-0.1:
      Successfully uninstalled gnip-analysis-pipeline-0.1
Successfully installed gnip-analysis-pipeline-0.1
/home/jmontague/Gnip-Analysis-Pipeline/tests
....................
----------------------------------------------------------------------
Ran 20 tests in 5.899s

OK
```

