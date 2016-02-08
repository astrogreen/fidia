'''
slogging: the SAMI Logging utility

This provides a simple logging utility suitable for use in SAMI modules.

Generically, one only needs to add the following lines to the top of a file:

    # Set up logging
    import slogging
    log = slogging.getLogger(__name__)
    log.setLevel(slogging.DEBUG)

Additional logging may be configured at the top of each file by, e.g.,

    log.add_file('/path/to/filename')
    log.enable_console_logging()

Then one can add messages to the log by calling, e.g.,

    log.debug("Just reached step n")
    log.info("More information")
    log.warning("I'm doing something stupid maybe you should pay attention")
    log.error("Bad things have just happened")

Logging levels are: (see https://docs.python.org/2/howto/logging.html)

    DEBUG   Detailed information, typically of interest only when diagnosing 
        problems.
    INFO    Confirmation that things are working as expected.
    WARNING An indication that something unexpected happened, or indicative of
        some problem in the near future (e.g. 'disk space low'). The software 
        is still working as expected.
    ERROR   Due to a more serious problem, the software has not been able to 
        perform some function.
    CRITICAL    A serious error, indicating that the program itself may be 
        unable to continue running.


History:

    Created on Apr 30, 2014 by Andy Green

    Module level configuration options updated 27 April 2015 by Andy Green


@author: agreen
'''

import os
import logging
import types


logging_configured = False
file_handler = None
console_handler = None

PACKAGE_LOGGER_NAME = 'fidia'

# Copy some things from parent package
DEBUG = logging.DEBUG
WARN = logging.WARN
WARNING = logging.WARNING
ERROR = logging.ERROR
INFO = logging.INFO

def configure_logging():
    
    # Set up logging for the package. Note that any modules who set up logging
    # below this package logger (using the `slogging.getLogger(__name__)` 
    # functionality) will propogate messages to this logger.
    #
    package_log = logging.getLogger(PACKAGE_LOGGER_NAME)

    # NOTE: The logging level should not be set here, but rather at the top of
    # each file. The setting below ensures that this logger will catch all 
    # requests from child loggers.
    package_log.setLevel(logging.DEBUG)

    try:
        if package_log.logging_configured: 
            return package_log
    except:
        pass

    # The code below should only ever be called once, so we raise an exception if this doesn't seem to be the case.
    # if len(package_log.handlers) > 0:
    #     raise Exception("Logging configured more than once for 'samiDB'")

    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s')

    # Default is to log messages to the 
    if 'SAMI_DB_LOG_FILE' in os.environ:
        filename = os.environ['SAMI_DB_LOG_FILE']
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        package_log.addHandler(file_handler)
    
    package_log.logging_configured = True

    return package_log

def add_file(self, filename):

    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s')

    global file_handler

    if file_handler is None:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
    self.addHandler(file_handler)

def enable_console_logging(self):

    global console_handler

    if console_handler is None:
        formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

    if console_handler not in self.handlers:
        self.addHandler(console_handler)

def disable_console_logging(self):

    if len(self.handlers) == 0:
        return

    global console_handler

    if console_handler is None:
        return
    
    for hndlr in self.handlers:
        if hndlr is console_handler:
            self.removeHandler(hndlr)

def getLogger(name):
    
    if not logging_configured:
        package_log = configure_logging()

    if PACKAGE_LOGGER_NAME != name[:len(PACKAGE_LOGGER_NAME)]:
        package_log.warn('Logging setup request for non-%s-package member "%s"', PACKAGE_LOGGER_NAME, name)

    log = logging.getLogger(name)

    # Add some convenience functions to the log object. 
    # See http://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object
    log.add_file = types.MethodType(add_file, log)
    log.enable_console_logging = types.MethodType(enable_console_logging, log)
    log.disable_console_logging = types.MethodType(disable_console_logging, log)

    return log
        