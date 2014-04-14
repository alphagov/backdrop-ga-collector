#! /usr/bin/env python2

import logging
import os

from backdrop.collector import arguments
from backdrop.collector.logging_setup import set_up_logging

if __name__ == '__main__':

    this_dir = os.path.dirname(os.path.realpath(__file__))
    repo_root = os.path.abspath(os.path.join(this_dir, ".."))

    logfile_path = os.path.join(repo_root, 'log')

    logging.basicConfig(level=logging.DEBUG)
    # set_up_logging('ga_collector_contrib_content', logging.INFO, logfile_path)

    # FIXME I do not condone path injection hacks like this. I would prefer if
    # this was setuptools-installed, but current consensus is that fixing this
    # would require updating too many other things to be consistent.
    from sys import path
    path[0:0] = [repo_root]
    from collector.contrib.content.table import main

    args = arguments.parse_args('Google Analytics')
    main(args)
