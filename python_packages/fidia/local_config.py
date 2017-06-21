"""
This module handles setting and loading the local configuration details for a given instance of Python/FIDIA.


Basically, the idea is that when FIDIA is loaded within a particular instance of
Python, it can load a configuration from file.  That configuration may do things
like set up an external Mapping Database or define a set of Data Access layers.

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Generator, Dict, Union
import fidia

# Standard Library Imports
import configparser
import os

# Other library imports

# FIDIA Imports

# Other modules within this FIDIA sub-package

from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

config = None

DEFAULT_CONFIG = """
[MappingDatabase]
engine = sqlite
location = 
database = :memory:
echo = False
"""

def find_config_files():
    """Identify a list of possible config files for use by FIDIA."""

    pwd = os.getcwd()
    fidia_package_dir = os.path.realpath(__file__)
    homedir = os.path.expanduser("~")
    fidia_config_dir = os.getenv('FIDIA_CONFIG_DIR', None)

    input_path_list = [
        (pwd, "fidia.ini"),
        (fidia_config_dir, "fidia.ini"),
        (homedir, ".fidia.ini"),
        (fidia_package_dir, "fidia.ini")
    ]

    output_path_list = []

    for path in input_path_list:
        if path[0] is None:
            continue
        string_path = os.path.join(*path)
        if os.path.exists(string_path):
            output_path_list.append(string_path)

    return output_path_list



def load_config(config_files):
    """Load a configuration from the supplied list of config files."""

    global config

    if config is not None:
        log.warn("FIDIA Config is being reloaded: should only be loaded once!")

    config = configparser.ConfigParser()
    config.read_string(DEFAULT_CONFIG)
    files_used = config.read(config_files)
    if log.isEnabledFor(slogging.DEBUG):
        for f in files_used:
            log.debug("Loaded FIDIA config from file: %s", f)

    return config

load_config(find_config_files())




