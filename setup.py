import os
from setuptools import setup, find_packages

from backdrop import collector

requirements = [
    'requests',
    'pytz',
    'argparse',
    'python-dateutil',
    'logstash_formatter'
]

setup(
    name='backdrop-ga-collector',
    version=collector.__VERSION__,
    packages=find_packages(exclude=['test*']),

    # metadata for upload to PyPI
    author=collector.__AUTHOR__,
    author_email=collector.__AUTHOR_EMAIL__,
    maintainer='Government Digital Service',
    url='https://github.com/alphagov/backdrop-ga-collector',

    description='backdrop-ga-collector send google analytics data to backdrop',
    license='MIT',
    keywords='api data performance_platform',

    install_requires=requirements,
)
